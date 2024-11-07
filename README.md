<!-- @format -->

# Remote System Monitor

A secure client-server application for remote system monitoring and management using Python sockets.

## Features

- Real-time system monitoring with secure client-server communication
- Detailed CPU information including usage, frequency and core count
- Memory statistics with RAM and swap usage tracking
- Disk space monitoring across mounted partitions
- Process management showing top 10 memory-intensive processes
- Network statistics including bytes/packets sent and received
- Restricted file system operations in allowed directories only
- Command-line interface with formatted output
- Cross-platform support (Windows/Linux)
- Logging and error handling
- Executable builds using PyInstaller

## Requirements

- Python 3.6+
- psutil
- tabulate
- pyinstaller

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Aum-Barai/New-folder--2-
   cd remote-system-monitor
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Build executables (optional):
   ```bash
   python build.py
   ```
   This will create standalone executables in the `dist` directory:
   - remote_server.exe (Windows) / remote_server (Linux)
   - remote_client.exe (Windows) / remote_client (Linux)
