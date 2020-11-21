# Using Paramiko to SSH into Maldbot Google VM
import base64
import paramiko
import io
import time
from pathlib import Path


# TODO: Tidy up the code. Functional code is in restart_bot, kill_process2, start_process2 functions
# Kills current running instance of MaldBot
def kill_process(client):
    stdin, stdout, stderr = client.exec_command('bash -l -c "ls;bash"', get_pty=True)
    print(type(stdout.readline()))
    print(stdout.readline())
    if len(stdout.readline()) > 1:
        pid = int(stdout.readline()) 
        client.exec_command(f'kill -9 {pid}')
        print(f'Killed pid: {pid}')
    '''
    pid = int(stdout.readline())
    if pid is not None:
        client.exec_command(f'kill -9 {pid}')
    '''

def kill_process2(shell):
    '''
    out = shell.recv(9999)
    shell.send('\nps aux\n')
    shell.send('pidof python bot2.py\n')
    print('first', out)
    if len(out.decode('ascii')) > 0:
        pid = out.decode('ascii')
        shell.send(f'\nkill -9 {pid}\n')
        print(f'Killed pid: {pid}')

    print(out.decode)
    '''
    # shell.exec_command('shopt -s expand_aliases')
    # stdin, stdout, stderr = shell.exec_command('/home/nicho/miniconda3/bin/conda activate GanGBot')
    stdin, stdout, stderr = shell.exec_command('/usr/bin/pidof python bot2.py')
    temp = stdout.readline().split()
    pids = []
    pids.extend(temp)

    if len(pids) > 0:
        stdin, stdout, stderr = shell.exec_command(f'/usr/bin/kill -9 {pids[0]}')

def start_process2(shell):
    stdin, stdout, stderr = shell.exec_command('/home/nicho/miniconda3/bin/conda activate GanGBot')
    stdin, stdout, stderr = shell.exec_command('/usr/bin/nohup /home/nicho/miniconda3/envs/GanGBot/bin/python /home/nicho/miniconda3/envs/GanGBot/bot2.py')

    # stdin, stdout, stderr = shell.exec_command(' ')

    
    # stdin, stdout, stderr = shell.exec_command('conda activate')
    # print(stdout.readline())

    '''
    shell.get_pty()
    stdin, stdout, stderr = shell.exec_command('echo $PATH')
    print(f'stdin: {stdin.readline() }\n stdout: {stdout.readline()}\n stderr: {stderr.readline()}')
    '''

    # shell.


def restart_bot(shell):
    kill_process2(shell)
    start_process2(shell)

def list_all(client, channel):
    out = channel.recv(9999)

    channel.send('ps aux\n')
    channel.send('pidof python bot2.py\n')
    channel.send('cd ~/miniconda3/envs/GanGBot/\n')
    channel.send('conda activate GanGBot\n')
    channel.send('nohup python bot2.py &\n')

    while not channel.recv_ready():
        time.sleep(3)

    out = channel.recv(9999)
    print(out.decode('ascii'))

    client.close()


    # channel = client.invoke_shell()
    # channel.send('ps aux')
    # channel.send('kill -9 29928')
    
    '''
    stdin, stdout, stderr = client.exec_command('cd ~')

    stdin, stdout, stderr = client.exec_command('sudo echo $PATH')
    print(stdout.readline())
    print('error', stderr.readline())
    '''
    

# Starts a MaldBot instance
def start_process(client):
    stdin, stdout, stderr = client.exec_command('cd ~/miniconda3/envs/GanGBot/', get_pty=True)
    print("stdout: ", stdout.readline())
    print('stderr: ', stderr.readline())


    stdin, stdout, stderr = client.exec_command('conda activate GanGBot', get_pty=True)
    print("stdout: ", stdout.readline())
    print('stderr: ', stderr.readline())
 

    stdin, stdout, stderr = client.exec_command('nohup python bot2.py &', get_pty=True)
    print("stdout: ", stdout.readline())
    print('stderr: ', stderr.readline())

def print_path(client):
    stdin, stdout, stderr = client.exec_command('sudo source "~/.bashrc"')
    print(stderr.readline())

    stdin, stdout, stderr = client.exec_command('bash -lc "echo $PATH"')
    print(stdout.readline())

    stdin, stdout, stderr = client.exec_command('ls')
    print(stdout.readline())

# Restarts a MaldBot instance
'''
def restart_bot(client):
    kill_process(client)
    start_process(client)
'''

key_path = Path(r"C:\Users\nicho\.ssh\maldbot.pem")
key = paramiko.RSAKey.from_private_key_file(key_path)
# the_string = "test"
host_key = paramiko.RSAKey(data=base64.b64decode(b'AAAAB3NzaC1yc2EAAAADAQABAAABAQC4vNFo2d9WVg47daoyawx1rcM9Pdva4QA4z0IcEP/oVz+VlkD/9semgf+Wj5NqP8wgEwhTi1xnY+grrkkVEeNMQpUShjSymwpHua6BdPMcKfsvjus6TkGUrXfox8BuRsdnvMbk6ITCIcMMsQMwZKYOL4iwQKB1ba+CnJzbOspqxQ5Xx0Rh8sWowx2etBsK7rcQ4oA/kaDpwBGKM6zYewJUCDjDnj3k0DrPJcdR4C/b8LNTdJfMuGYoTHXpRxzNKgFOWlooJh9HkXO6tAYPXRkAMQ6xy5qvS8epM63dgPA3y6RX8/o+i4Feeb9FcpF0AQ5UsTOmRjnGyHPhPVm09M4j'))
client = paramiko.SSHClient()

client.get_host_keys().add('34.87.24.87', 'ssh-rsa', host_key)
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('34.87.24.87', username='nicho', pkey=key)

channel = client.invoke_shell()


# kill_process(client)
# start_process(client)
# restart_bot(client)
# list_all(client, channel)
# time.sleep(10)
# print_path(client)
restart_bot(client)


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