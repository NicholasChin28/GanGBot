# Using Paramiko to SSH into Maldbot Google VM
# TODO: After running nohup to launch the bot, exit from the terminal 
# TODO: Update bot with gitpython
import base64
import paramiko
import io
import time
from pathlib import Path
from dotenv import dotenv_values




# Kills current running instance of MaldBot
# TODO: Consider running python_file from .sh file
def kill_process(client):
    # Kills all screens
    # Temporary fix
    # TODO: Find the screen that is attached to bot.py PID and kill that specific screen and PID
    stdin, stdout, stderr = client.exec_command(f'pkill screen')
    print('Output kill: ', stdout.readline())
    print('Error kill: ', stderr.readline())
    
def get_process(client):
    # stdin, stdout, stderr = client.exec_command('pidof python bot2.py')
    stdin, stdout, stderr = client.exec_command(f'pidof {env_vals["PYTHON_PATH"]} {env_vals["PYTHON_FILE"]} ')
    print('Output: ', stdout.readline())
    print('Error: ', stderr.readline())

def start_process(client):
    stdin, stdout, stderr = client.exec_command(f'{env_vals["CONDA_PATH"]} activate GanGBot')
    print('Output activate: ', stdout.readline())
    print('Error activate: ', stderr.readline())

    # Uses screen instead of nohup to restore control to terminal after finishing commands
    stdin, stdout, stderr = client.exec_command(f'screen -dm {env_vals["PYTHON_PATH"]} {env_vals["PYTHON_FILE"]}')
    print('Output nohup: ', stdout.readline())
    print('Error nohup: ', stderr.readline())

    client.close()

def restart_bot(client):
    kill_process(client)
    start_process(client)

def print_path(client):
    stdin, stdout, stderr = client.exec_command('sudo source "~/.bashrc"')
    print(stderr.readline())

    stdin, stdout, stderr = client.exec_command('bash -lc "echo $PATH"')
    print(stdout.readline())

    stdin, stdout, stderr = client.exec_command('ls')
    print(stdout.readline())

# Function / method to stop running instance / all instances of Maldbot
def stop_bot(client):
    kill_process(client)


env_vals = dotenv_values('.env')

key_path = Path(f"{env_vals['PEM_FILE']}")
key = paramiko.RSAKey.from_private_key_file(key_path)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('34.87.24.87', username='nicho', pkey=key)

channel = client.invoke_shell()

restart_bot(client)
# get_process(client)
# client.close()
