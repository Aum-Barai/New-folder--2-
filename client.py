import socket
import logging
import sys
import json
from tabulate import tabulate
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RemoteClient:
    """
    A client for connecting to the remote monitoring server and executing commands.
    
    This client provides a command-line interface for interacting with the remote server,
    formatting responses, and maintaining the connection.
    
    Attributes:
        host (str): The server host to connect to (default: '127.0.0.1')
        port (int): The server port to connect to (default: 65432)
        socket (socket.socket): The client socket object
    
    Example:
        >>> client = RemoteClient(host='server_ip', port=65432)
        >>> client.start_client()
    """
    
    def __init__(self, host='127.0.0.1', port=65432):
        """
        Initialize the RemoteClient with server host and port.
        
        Args:
            host (str): The server host to connect to
            port (int): The server port to connect to
        """
        self.host = host
        self.port = port
        self.socket = None
        
    def connect(self):
        """Connect to the remote server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logging.info(f"Connected to server at {self.host}:{self.port}")
            return True
        except Exception as e:
            logging.error(f"Connection failed: {str(e)}")
            return False

    def send_command(self, command):
        """Send command to server and receive response"""
        try:
            self.socket.send(command.encode())
            response = self.socket.recv(4096).decode()
            return response
        except Exception as e:
            logging.error(f"Error sending command: {str(e)}")
            return None

    def start_client(self):
        """Start client interface"""
        if not self.connect():
            return

        self.show_help()
        
        try:
            while True:
                command = input("\nEnter command: ").strip()
                if not command:
                    continue

                response = self.send_command(command)
                if response:
                    self.format_response(command, response)
                
                if command.lower() == 'exit':
                    break

        except KeyboardInterrupt:
            print("\nClient shutting down...")
        finally:
            self.cleanup()

    def format_response(self, command, response):
        """Format the response based on command type"""
        print("\nServer response:")
        
        try:
            # Try to parse response as JSON
            data = json.loads(response)
            
            if command.startswith('processes'):
                # Format process list as table
                headers = ['PID', 'Name', 'Memory %']
                rows = [[p['pid'], p['name'], f"{p.get('memory_percent', 0):.1f}%"] 
                       for p in data]
                print(tabulate(rows, headers=headers, tablefmt='grid'))
                
            elif command.startswith(('cpu', 'memory', 'netstat', 'diskspace')):
                # Pretty print JSON data
                print(json.dumps(data, indent=2))
                
            elif command.startswith('listdir'):
                # Format directory listing
                print(f"\nContents of {data['path']}:")
                for item in data['contents']:
                    print(f"  {item}")
            else:
                print(response)
                
        except json.JSONDecodeError:
            # If not JSON, print as plain text
            print(response)

    def show_help(self):
        """Show available commands"""
        commands = """
Available Commands:
-----------------
System Information:
  sysinfo  - Get detailed system information
  cpu      - Get CPU usage and information
  memory   - Get memory usage statistics
  diskspace- Get disk space information

Process Management:
  processes- List top 10 processes by memory usage

Network:
  netstat  - Get network statistics
  time     - Get server time

File Operations:
  listdir [path] - List contents of allowed directories

Other:
  echo <message> - Echo a message
  exit          - Close connection
"""
        print(commands)

    def cleanup(self):
        """Clean up client resources"""
        if self.socket:
            self.socket.close()
        logging.info("Client cleaned up and shut down")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Remote Client')
    parser.add_argument('--host', default='127.0.0.1', help='Server host to connect to')
    parser.add_argument('--port', type=int, default=65432, help='Server port to connect to')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    client = RemoteClient(host=args.host, port=args.port)
    client.start_client() 