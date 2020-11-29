# Using Paramiko to SSH into Maldbot Google VM
import base64
import paramiko
import io
import time
from pathlib import Path
from dotenv import dotenv_values




# Kills current running instance of MaldBot
# TODO: Consider running python_file from .sh file
def kill_process(client):
    stdin, stdout, stderr = client.exec_command(f'pidof {env_vals["PYTHON_PATH"]} {env_vals["PYTHON_FILE"]} ')
    temp = stdout.readline().split()
    pids = []
    pids.extend(temp)

    if len(pids) > 0:
        stdin, stdout, stderr = client.exec_command(f'kill -9 {pids[0]}')

def get_process(client):
    # stdin, stdout, stderr = client.exec_command('pidof python bot2.py')
    stdin, stdout, stderr = client.exec_command(f'pidof {env_vals["PYTHON_PATH"]} {env_vals["PYTHON_FILE"]} ')
    print('Output: ', stdout.readline())
    print('Error: ', stderr.readline())

def start_process(client):
    stdin, stdout, stderr = client.exec_command(f'{env_vals["CONDA_PATH"]} activate GanGBot')
    print('Output activate: ', stdout.readline())
    print('Error activate: ', stderr.readline())

    stdin, stdout, stderr = client.exec_command(f'nohup {env_vals["PYTHON_PATH"]} {env_vals["PYTHON_FILE"]}')
    print('Output nohup: ', stdout.readline())
    print('Error nohup: ', stderr.readline())


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


env_vals = dotenv_values('.env')

key_path = Path(f"{env_vals['PEM_FILE']}")
key = paramiko.RSAKey.from_private_key_file(key_path)
# the_string = "test"
host_key = paramiko.RSAKey(data=base64.b64decode(b'AAAAB3NzaC1yc2EAAAADAQABAAABAQC4vNFo2d9WVg47daoyawx1rcM9Pdva4QA4z0IcEP/oVz+VlkD/9semgf+Wj5NqP8wgEwhTi1xnY+grrkkVEeNMQpUShjSymwpHua6BdPMcKfsvjus6TkGUrXfox8BuRsdnvMbk6ITCIcMMsQMwZKYOL4iwQKB1ba+CnJzbOspqxQ5Xx0Rh8sWowx2etBsK7rcQ4oA/kaDpwBGKM6zYewJUCDjDnj3k0DrPJcdR4C/b8LNTdJfMuGYoTHXpRxzNKgFOWlooJh9HkXO6tAYPXRkAMQ6xy5qvS8epM63dgPA3y6RX8/o+i4Feeb9FcpF0AQ5UsTOmRjnGyHPhPVm09M4j'))
client = paramiko.SSHClient()

client.get_host_keys().add('34.87.24.87', 'ssh-rsa', host_key)
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('34.87.24.87', username='nicho', pkey=key)

channel = client.invoke_shell()



restart_bot(client)
# get_process(client)
client.close()
