import sys
import os
import socket
import json
import subprocess
import platform
import tempfile
import time
from typing import Optional
from utils.colors import Colors
# Keep your existing imports
from interface.delivery import Delivery
from schemas.in_game import Character

class TerminalDelivery(Delivery):
    """
    A class that acts as a proxy, sending I/O requests to a separate 
    terminal window via a local socket connection.
    """

    def __init__(self):
        self.conn = None
        self.worker_file = None
        self._launch_remote_terminal()

    def _launch_remote_terminal(self):
        """Sets up a socket server and launches the worker in a new window."""
        # 1. Create a local server to listen for the new terminal
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('localhost', 0)) # 0 lets the OS pick a free port
        server.listen(1)
        host, port = server.getsockname()

        # 2. Define the code that will run inside the NEW terminal
        # This acts as a 'dumb terminal' that just processes print/input commands
        worker_script = f"""
import socket, json, sys, os

def run_worker():
    try:
        # Connect back to the main game engine
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('{host}', {port}))
        print(f"\\033[32mConnected to Game Engine on port {port}...\\033[0m")
        
        while True:
            # Wait for command from main app
            data = s.recv(4096)
            if not data: break # Connection closed
            
            msg = json.loads(data.decode('utf-8'))
            
            if msg['type'] == 'print':
                print(msg['text'])
                
            elif msg['type'] == 'input':
                # Perform input in this window and send result back
                user_response = input(msg['prompt'])
                s.send(json.dumps(user_response).encode('utf-8'))
                
    except Exception as e:
        print(f"Connection lost or error: {{e}}")
        input("Press Enter to close this window...")

if __name__ == "__main__":
    run_worker()
"""

        # 3. Write this code to a temporary file
        fd, self.worker_file = tempfile.mkstemp(suffix=".py")
        os.write(fd, worker_script.encode())
        os.close(fd)

        # 4. Launch that file in a new OS-specific terminal window
        self._spawn_terminal_window(self.worker_file)

        # 5. Wait for the new window to connect back to us
        print("Waiting for external terminal to connect...")
        self.conn, addr = server.accept()
        print(f"External terminal connected.")
        server.close() # Stop listening, we have our connection

    def _spawn_terminal_window(self, script_path):
        """Handles the OS differences for opening a new window."""
        system_platform = platform.system()
        python_exe = sys.executable  # Use the same python interpreter (e.g. venv)

        if system_platform == "Windows":
            # 'start cmd /k' opens a new Command Prompt and keeps it open
            subprocess.Popen(f'start cmd /k "{python_exe} "{script_path}""', shell=True)
        
        elif system_platform == "Darwin": # macOS
            # Use AppleScript to tell Terminal.app to run the script
            cmd = f'tell application "Terminal" to do script "{python_exe} {script_path}"'
            subprocess.Popen(["osascript", "-e", cmd])
            
        elif system_platform == "Linux":
            # Try common linux terminal emulators
            if os.path.exists("/usr/bin/gnome-terminal"):
                subprocess.Popen(["gnome-terminal", "--", python_exe, script_path])
            elif os.path.exists("/usr/bin/xterm"):
                subprocess.Popen(["xterm", "-e", python_exe, script_path])
            else:
                print("Error: Could not find gnome-terminal or xterm.")

    def master_message(self, text: str, tag: str | None = None):
        """Sends a print command to the external terminal."""
        if not self.conn: return
        
        # Prepare the ANSI formatted string here in the main app
        formatted_text = Colors.colorize(
            text=f"DM {tag if tag else ''}: {text}", 
            color_code=Colors.BRIGHT_BLACK)
        
        payload = {'type': 'print', 'text': formatted_text}
        self._send_payload(payload)

    def player_request(self, character: Character):
        """Sends an input command to the external terminal and waits for response."""
        if not self.conn: return ""

        prompt = (
            f"Player {character.name}, enter your action "
            f"(current position: ({character.position.x}, "
            f"{character.position.y})): "
        )
        prompt = Colors.colorize(prompt, Colors.BRIGHT_MAGENTA)
        payload = {'type': 'input', 'prompt': prompt}
        self._send_payload(payload)
        
        # This blocks until the other window sends the user's input back
        response_json = self.conn.recv(4096).decode('utf-8')
        return json.loads(response_json)

    def _send_payload(self, payload):
        try:
            self.conn.send(json.dumps(payload).encode('utf-8')) # type: ignore
        except BrokenPipeError:
            print("Error: External terminal disconnected.")

    def __del__(self):
        """Cleanup temporary file and connection on exit."""
        if self.conn:
            self.conn.close()
        if self.worker_file and os.path.exists(self.worker_file):
            try:
                os.remove(self.worker_file)
            except:
                pass