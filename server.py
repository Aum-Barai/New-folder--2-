import socket
import platform
import subprocess
import sys
from datetime import datetime
import logging
import os
import psutil
import json
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RemoteServer:
    """
    A secure remote monitoring server that provides system information and monitoring capabilities.
    
    This server implements various monitoring commands and restricts operations to maintain security.
    It uses socket programming for network communication and includes comprehensive logging.
    
    Attributes:
        host (str): The host address to bind to (default: '127.0.0.1')
        port (int): The port to listen on (default: 65432)
        socket (socket.socket): The server socket object
        client (socket.socket): The connected client socket
        addr (tuple): The address info of the connected client
        allowed_dirs (list): List of directories allowed for file operations
    
    Example:
        >>> server = RemoteServer(host='0.0.0.0', port=65432)
        >>> server.start_server()
    """
    
    def __init__(self, host='127.0.0.1', port=65432):
        """
        Initialize the RemoteServer with host and port.
        
        Args:
            host (str): The host address to bind to
            port (int): The port to listen on
        """
        self.host = host
        self.port = port
        self.socket = None
        self.client = None
        self.addr = None
        # Define allowed directories for file operations
        self.allowed_dirs = ['./shared', './downloads']
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in self.allowed_dirs:
            os.makedirs(directory, exist_ok=True)

    def start_server(self):
        """Start the server and listen for connections"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Enable address reuse
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            logging.info(f"Server listening on {self.host}:{self.port}")
            
            self.client, self.addr = self.socket.accept()
            logging.info(f"Connection from {self.addr}")
            
            self.handle_client()
            
        except Exception as e:
            logging.error(f"Server error: {str(e)}")
        finally:
            self.cleanup()

    def handle_client(self):
        """Handle client commands"""
        while True:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    break
                
                response = self.process_command(data)
                self.client.send(response.encode())
                
            except ConnectionResetError:
                logging.error("Client disconnected unexpectedly")
                break
            except Exception as e:
                logging.error(f"Error handling client: {str(e)}")
                break

    def process_command(self, command):
        """Process received commands and return appropriate response"""
        command = command.strip().lower()
        
        # Extended dictionary of allowed commands
        commands = {
            'sysinfo': self.get_system_info,
            'time': self.get_time,
            'echo': self.echo_message,
            'exit': self.exit_connection,
            'cpu': self.get_cpu_info,
            'memory': self.get_memory_info,
            'processes': self.get_running_processes,
            'netstat': self.get_network_stats,
            'listdir': self.list_directory,
            'diskspace': self.get_disk_space
        }
        
        # Parse command and arguments
        cmd_parts = command.split(' ', 1)
        cmd = cmd_parts[0]
        args = cmd_parts[1] if len(cmd_parts) > 1 else ''
        
        if cmd in commands:
            return commands[cmd](args)
        return "Invalid command. Use 'help' to see available commands."

    def get_system_info(self, args):
        """Return basic system information"""
        return f"""
System Information:
OS: {platform.system()} {platform.version()}
Machine: {platform.machine()}
Processor: {platform.processor()}
"""

    def get_time(self, args):
        """Return current server time"""
        return f"Server time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def echo_message(self, message):
        """Echo the received message"""
        return f"Echo: {message}"

    def exit_connection(self, args):
        """Handle exit command"""
        self.cleanup()
        return "Server shutting down..."

    def cleanup(self):
        """Clean up server resources"""
        if self.client:
            self.client.close()
        if self.socket:
            self.socket.close()
        logging.info("Server cleaned up and shut down")

    def get_cpu_info(self, args):
        """Get detailed CPU information"""
        cpu_info = {
            'cpu_percent': psutil.cpu_percent(interval=1, percpu=True),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
            'cpu_count': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count()
        }
        return json.dumps(cpu_info, indent=2)

    def get_memory_info(self, args):
        """Get system memory information"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        mem_info = {
            'total': f"{memory.total / (1024**3):.2f} GB",
            'available': f"{memory.available / (1024**3):.2f} GB",
            'percent_used': f"{memory.percent}%",
            'swap_total': f"{swap.total / (1024**3):.2f} GB",
            'swap_used': f"{swap.used / (1024**3):.2f} GB"
        }
        return json.dumps(mem_info, indent=2)

    def get_running_processes(self, args):
        """Get list of running processes (top 10 by memory usage)"""
        processes = []
        for proc in sorted(psutil.process_iter(['pid', 'name', 'memory_percent']), 
                          key=lambda x: x.info['memory_percent'] or 0, 
                          reverse=True)[:10]:
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return json.dumps(processes, indent=2)

    def get_network_stats(self, args):
        """Get network statistics"""
        net_stats = psutil.net_io_counters()
        return json.dumps({
            'bytes_sent': f"{net_stats.bytes_sent / (1024**2):.2f} MB",
            'bytes_recv': f"{net_stats.bytes_recv / (1024**2):.2f} MB",
            'packets_sent': net_stats.packets_sent,
            'packets_recv': net_stats.packets_recv
        }, indent=2)

    def list_directory(self, path=''):
        """List contents of allowed directories"""
        try:
            # Ensure the requested path is within allowed directories
            requested_path = os.path.abspath(os.path.join('.', path.strip()))
            if not any(requested_path.startswith(os.path.abspath(allowed)) 
                      for allowed in self.allowed_dirs):
                return "Access denied. Path not in allowed directories."
            
            items = os.listdir(requested_path)
            return json.dumps({
                'path': requested_path,
                'contents': items
            }, indent=2)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def get_disk_space(self, args):
        """Get disk space information"""
        disk_info = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info[partition.mountpoint] = {
                    'total': f"{usage.total / (1024**3):.2f} GB",
                    'used': f"{usage.used / (1024**3):.2f} GB",
                    'free': f"{usage.free / (1024**3):.2f} GB",
                    'percent': f"{usage.percent}%"
                }
            except Exception:
                continue
        return json.dumps(disk_info, indent=2)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Remote Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=65432, help='Port to bind to')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    server = RemoteServer(host=args.host, port=args.port)
    server.start_server() 