import subprocess
import json
import re
import socket
import os
import time
from PasswordEncryption import *

def get_hostname():
    return socket.gethostname()

def load_config():
    """Load configuration from config.json."""
    with open("config.json", "r") as file:
        return json.load(file)

def run_command_on_host(ssh_client,command):
        try: 
            stdin, stdout, stderr = ssh_client.exec_command(command)
            output = stdout.read().decode('ascii')
            print("command : " + command)
            print("output: " + output)
            lines = output.splitlines()
            return lines
        except Exception as e:
            tb = traceback.format_exc()
            print(f"An unexpected error occurred: {tb}")
            return None


def monitor_log_on_node(node, logfile, error_string, action,cache_file=".log_monitor_cache"):
    
    """Monitor the log file on the given node."""
    print(f"Monitoring log file '{logfile}' for errors on node '{node}'...")
    # This is a placeholder for accessing the log file remotely (e.g., via SSH)
    # Implement log monitoring logic here based on your node access method.
    hostname = get_hostname()
    if hostname == node or node=="localhost": # Tail has to be done on the same server
        # Get the last line number from the cache
        last_line_num = 0
        if os.path.exists(cache_file):
            with open(cache_file, "r") as cf:
                try:
                    last_line_num = int(cf.read().strip())
                except ValueError:
                    last_line_num = 0

        # Read the log file starting from the last line number
        try:
            with open(logfile, "r") as log:
                lines = log.readlines()
                new_lines = lines[last_line_num:]
                
                for line in new_lines:
                    if error_string in line:
                        print(action)
                        break  # Stop after first match (optional)

            # Update the cache with the new last line number
            with open(cache_file, "w") as cf:
                cf.write(str(len(lines)))

        except FileNotFoundError:
            print(f"Log file '{logfile}' not found.")
   

import os
import subprocess
import hashlib

def monitor_podman_service_on_node(node, service, error_string, action):
    # Use a unique cache file per (node + service)
    unique_id = hashlib.md5(f"{node}_{service}".encode()).hexdigest()
    cache_file = f".log_monitor_cache_{unique_id}" 

    last_line = 0
    if os.path.exists(cache_file):
        with open(cache_file, "r") as cf:
            try:
                last_line = int(cf.read().strip())
            except ValueError:
                last_line = 0

    # Fetch full logs of the Podman service
    try:
        result = subprocess.run(
            ["podman", "logs", service],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"Failed to get logs for service '{service}': {result.stderr.strip()}")
            return

        log_lines = result.stdout.splitlines()
        new_logs = log_lines[last_line:]

        for line in new_logs:
            if error_string in line:
                print(action)
                break  # Only one action per check

        # Save new last line position
        with open(cache_file, "w") as cf:
            cf.write(str(len(log_lines)))

    except subprocess.TimeoutExpired:
        print(f"Timeout while reading logs for {service}")
    except Exception as e:
        print(f"Error monitoring service '{service}': {e}")



if __name__ == "__main__":
    file_prefix = ""
    configurationFile = file_prefix + "etc/config.json"
    keyFile = file_prefix + "env/key.txt"
    with open(keyFile,"r") as keyfile:
        key=keyfile.read()
    EncryptConfigurationFile(configurationFile,keyFile,"CustomerDetails")
    # Load configuration
    config = load_config()
    service_name = config.get("service_name")
    logfile = config.get("logfile")
    error_string = config.get("error_string")
    action = config.get("action")

    if not service_name or not logfile or not error_string or not action:
        print("Invalid configuration. Please check config.json.")
        exit(1)
    monitor_log_on_node("localhost", logfile, error_string, action)