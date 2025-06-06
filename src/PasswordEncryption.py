import json
import os
from cryptography.fernet import Fernet
from logger_config import logger

def EncryptPassword(password,key):
    cipher_suite = Fernet(key)
    if not isinstance(password, dict):
        encryptedPassword = cipher_suite.encrypt(password.encode('utf-8'))
        #password_hash = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
        #salt_base64 = base64.b64encode(salt).decode('utf-8')
        #key_base64 = base64.b64encode(key).decode('utf-8')
        return {"EncryptedPwd":encryptedPassword.decode('utf-8')}
    else:
        return password
        

def DecryptPassword(password,key):
    cipher_suite = Fernet(key)
    plainPwd = cipher_suite.decrypt(password).decode('utf-8')
    return plainPwd

def EncryptConfigurationFile(config_file,keyFile,passwordKey):
    #config_file = "configuration_copy.json"
    #keyFile="key.txt"
    with open(keyFile,"r") as keyfile:
        key=keyfile.read()

    try:
        # Check if the file exists before attempting to load it
        if not os.path.exists(config_file):
            logger.error(f"File '{config_file}' does not exist.")
            exit()

        # Load the existing configuration from the file
        with open(config_file, "r") as f:
            try:
                config = json.load(f)
            except json.decoder.JSONDecodeError as e:
                logger.error(f"Error loading JSON data: {e}")
                exit()
    except FileNotFoundError:
        logger.error(f"File '{config_file}' not found. Make sure it exists.")
        exit()

    # Update the password in the loaded configuration
   
 
    appDict = config[passwordKey]
    for cust in config[passwordKey]:
        cmSshPwd = cust["sshPassword"]
        apiPwd = cust["APIPassword"]

        encrypteSshPwd = EncryptPassword(cmSshPwd,key)
        encrypteApiPwd = EncryptPassword(apiPwd,key)
        config[passwordKey]["sshPassword"] = encrypteSshPwd
        config[passwordKey]["APIPassword"] = encrypteApiPwd
        for hosts in cust["hosts"]:
            
   

    
    # Save the updated configuration back to the file
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)  # You can use `indent` to format the JSON for readability

   