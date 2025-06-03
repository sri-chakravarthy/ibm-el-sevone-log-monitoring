import subprocess
import json
import re
import socket
import os
import time

def get_hostname():
    return socket.gethostname()

def load_config():
    """Load configuration from config.json."""
    with open("config.json", "r") as file:
        return json.load(file)

def get_ssh_client(nodeName):
        ssh_client = paramiko.SSHClient()
        try: 
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f"Node: {Node}")
            print(f"Using sskeys for ssh")
            private_key = paramiko.RSAKey.from_private_key_file("/root/.ssh/id_rsa")
            ssh_client.connect(nodeName, pkey=private_key)
            return ssh_client
        except Exception as e:
            tb = traceback.format_exc()
            logger.critical(f"An unexpected error occurred: {tb}")
            return None


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


def get_node_for_kube_service(service_name):
    """Find the node where the service (pod) is running."""
    try:
        # Execute kubectl command to get pod details
        result = subprocess.run(
            ["kubectl", "get", "pods", "-o", "wide"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )
        pods_output = result.stdout
        column_names = pods_output.splitlines()[0].split()
        i=0
        col_found=0
        for col in column_names:
            print(col)
            if col == "NODE":
               col_found=1
               break;
            i+=1
        if col_found==1:
           print(f"Node is col: {i}")
        else:
           print("Node not found")        
           return None
        # Parse the output to find the node for the service
        for line in pods_output.splitlines():
            if service_name in line:
                node = line.split()[i]
                #match = re.search(r"\s(\S+)\s*$", line)  # Extract the last column (Node)
                #if match:
                #    return match.group(1)  # Node name
                return node
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error running kubectl: {e.stderr}")
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
   



def tail_log_file(logfile):
    with open(logfile, "r") as file:
        lines = file.readlines()
        print(lines)
        file.seek(0, os.SEEK_END)  # Start reading at the end of the file
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)  # Wait for new lines
                continue
            print(line)
            yield line

def raise_alert(message):
    print(f"ALERT: {message}")




def monitor_kube_service():
    
    # Get the node where the service is running
    node = get_node_for_kube_service(service_name)
    if node:
        print(f"Service '{service_name}' is running on node '{node}'.")
        # Monitor log file on the identified node
        monitor_log_on_node(node, logfile, error_string, action)
    else:
        print(f"Service '{service_name}' not found.")



if __name__ == "__main__":
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
