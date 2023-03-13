"""Launcher"""

import subprocess

PROCESSES = []

while True:
    ACTION = input('Choice action: q - exit, '
                's - start server and clients, '
                'x - close all process: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        PROCESSES.append(subprocess.Popen('python3 server.py',
                                        creationflags=subprocess.CREATE_NEW_CONSOLE()))
        PROCESSES.append(subprocess.Popen('python3 client.py -n test1',
                                        creationflags=subprocess.CREATE_NEW_CONSOLE()))
        PROCESSES.append(subprocess.Popen('python3 client.py -n test2',
                                        creationflags=subprocess.CREATE_NEW_CONSOLE()))
        PROCESSES.append(subprocess.Popen('python3 client.py -n test3',
                                        creationflags=subprocess.CREATE_NEW_CONSOLE()))
    elif ACTION == 'x':
        while PROCESSES:
            VICTIM = PROCESSES.pop()
            VICTIM.kill()