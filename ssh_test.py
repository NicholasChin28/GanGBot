# Using Paramiko to SSH into Maldbot Google VM
import base64
import paramiko
import io
import time
from pathlib import Path

# Kills current running instance of MaldBot
def kill_process(client):
    stdin, stdout, stderr = client.exec_command('pidof python bot2.py')
    print(type(stdout.readline()))
    print(stderr.readline())
    if len(stdout.readline()) > 1:
        pid = int(stdout.readline()) 
        client.exec_command(f'kill -9 {pid}')
    '''
    pid = int(stdout.readline())
    if pid is not None:
        client.exec_command(f'kill -9 {pid}')
    '''

# Starts a MaldBot instance
def start_process(client):
    stdin, stdout, stderr = client.exec_command('cd ~/miniconda3/envs/GanGBot/')
    print("stdout: ", stdout.readline())
    print('stderr: ', stderr.readline())


    stdin, stdout, stderr = client.exec_command('conda activate GanGBot')
    print("stdout: ", stdout.readline())
    print('stderr: ', stderr.readline())


    stdin, stdout, stderr = client.exec_command('nohup python bot2.py &; sleep 10', get_pty=True)
    print("stdout: ", stdout.readline())
    print('stderr: ', stderr.readline())

# Restarts a MaldBot instance
def restart_bot(client):
    kill_process(client)
    start_process(client)

key_path = Path(r"C:\Users\nicho\.ssh\maldbot.pem")
key = paramiko.RSAKey.from_private_key_file(key_path)
# the_string = "test"
host_key = paramiko.RSAKey(data=base64.b64decode(b'AAAAB3NzaC1yc2EAAAADAQABAAABAQC4vNFo2d9WVg47daoyawx1rcM9Pdva4QA4z0IcEP/oVz+VlkD/9semgf+Wj5NqP8wgEwhTi1xnY+grrkkVEeNMQpUShjSymwpHua6BdPMcKfsvjus6TkGUrXfox8BuRsdnvMbk6ITCIcMMsQMwZKYOL4iwQKB1ba+CnJzbOspqxQ5Xx0Rh8sWowx2etBsK7rcQ4oA/kaDpwBGKM6zYewJUCDjDnj3k0DrPJcdR4C/b8LNTdJfMuGYoTHXpRxzNKgFOWlooJh9HkXO6tAYPXRkAMQ6xy5qvS8epM63dgPA3y6RX8/o+i4Feeb9FcpF0AQ5UsTOmRjnGyHPhPVm09M4j'))
client = paramiko.SSHClient()

client.get_host_keys().add('34.87.24.87', 'ssh-rsa', host_key)
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('34.87.24.87', username='nicho', pkey=key)

# start_process(client)
restart_bot(client)
time.sleep(10)

'''
stdin, stdout, stderr = client.exec_command('pidof python bot2.py')
pid = int(stdout.readline())
# pid_test = stdout.readline()
print('Process id: ', pid)
'''

# Functions here
# restart_bot(client)

'''
stdin, stdout, stderr = client.exec_command('pidof python bot2.py')
pid = int(stdout.readline())
print('Process id: ', pid)
'''

client.close()
'''
stdin, stdout, stderr = client.exec_command('ls')
for line in stdout:
    print('... ' + line.strip('\n'))
client.close()
'''