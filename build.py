import os
import platform
import shutil

def clean_directories():
    """Clean build and dist directories"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

def build_executables():
    """Build executables for client and server"""
    # Clean previous builds
    clean_directories()
    
    # Determine the appropriate file extension
    ext = '.exe' if platform.system() == 'Windows' else ''
    
    # Build commands
    commands = [
        f'pyinstaller --onefile --name remote_server{ext} server.py',
        f'pyinstaller --onefile --name remote_client{ext} client.py'
    ]
    
    # Execute build commands
    for cmd in commands:
        os.system(cmd)
    
    print("\nBuild completed!")
    print(f"\nExecutables can be found in the 'dist' directory:")
    print(f"- remote_server{ext}")
    print(f"- remote_client{ext}")

if __name__ == "__main__":
    build_executables() 