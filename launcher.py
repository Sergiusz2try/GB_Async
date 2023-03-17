"""Программа-лаунчер"""

import subprocess

PROCESSES = []

while True:
    ACTION = input('Выберите действие: q - выход, '
                's - запустить сервер и клиенты, '
                'x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        users_count = input("Введите кол-во пользователей: ")

        PROCESSES.append(subprocess.Popen('python server.py',
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(1, users_count+1):
            PROCESSES.append(subprocess.Popen(f'python client.py -n test{i}',
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif ACTION == 'x':
        while PROCESSES:
            VICTIM = PROCESSES.pop()
            VICTIM.kill()