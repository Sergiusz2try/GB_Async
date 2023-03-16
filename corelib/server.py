import argparse
import select
from socket import *
import sys
import time
from corelib import jim, config
from corelib.utils import get_message, send_message
from corelib.variables import ACCOUNT_NAME, ACTION, DEFAULT_PORT, DESTINATION, ERROR, EXIT, MAX_CONNECTIONS, MESSAGE, MESSAGE_TEXT, PRESENCE, RESPONSE_400, SENDER, TIME, USER
from logs.server_log_config import LOG
from corelib.decos import log


@log
def arg_parser():
    """Парсер аргументов коммандной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_addr = namespace.a
    listen_port = namespace.p

    # проверка получения корретного номера порта для работы сервера.
    if not 1023 < listen_port < 65536:
        LOG.critical(
            f'Попытка запуска сервера с указанием неподходящего порта {listen_port}. '
            f'Допустимы адреса с 1024 до 65535.')
        sys.exit(1)

    return listen_addr, listen_port


# @log
# def get_options(args, options_file):
#     '''
#     Get server options
#     :param args: Command line arguments
#     :param options_file: Options file name
#     :return: dict
#     '''
#     options = config.get_json_options(options_file)
#     cl_options = config.get_command_options(args, "a:p:")
#     for opt in cl_options:
#         if opt[0] == "-a":
#             options["DEFAULT"]["HOST"] = opt[1]
#         elif opt[0] == "-p":
#             options["DEFAULT"]["PORT"] = opt[1]

#     listen_addr = options["DEFAULT"]["HOST"]
#     listen_port = options["DEFAULT"]["PORT"]

#     return listen_addr, listen_port


@log
def process_client_message(message, messages_list, client, clients, names):
    """
    Message handler from clients, accepts a dictionary - a message from the client,
    checks the correctness, sends a response dictionary to the client with the result of the reception.
    :param message:
    :param messages_list:
    :param client:
    :param clients:
    :param names:
    :return:
    """

    LOG.debug(f"Received message from client: {message}")
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message:
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, response_200())
        else:
            response = RESPONSE_400
            response[ERROR] = "Username already exist."
            send_message(client, response)
            clients.remove(client)
            client.close()
        return
    # If it message add it to message list
    elif ACTION in message and message[ACTION] == MESSAGE and \
            DESTINATION in message and TIME in message and \
            SENDER in message and MESSAGE_TEXT in message:
        messages_list.append(message)
        return
    # If client exit.
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    # Else bad request.
    else:
        send_message(client, response_400())
        return
    

@log
def process_message(message, names, listen_socks):
    """
    Function address sended message correct user. Get dict message,
    list registered users and listen sockets. Nothing return.
    :param message:
    :param names:
    :param listen_socks:
    :return:
    """
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        LOG.info(f"Sended message for user: {message[DESTINATION]}"
                f"from user {message[SENDER]}")
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        LOG.error(f"User {message[DESTINATION]} are not registered on the server.")


@log
def response_200():
    msg = {
        "response": 200,
        "alert": "OK"
    }

    return msg


@log
def response_400():
    msg = {
        "response": 400,
        "alert": "Bad request"
    }

    return msg


def run():
    '''
    Run server
    :param args: Command line arguments
    :return:
    '''
    listen_addr, listen_port = arg_parser()

    LOG.info(
        f'Start server, port for connection: {listen_port}, '
    )

    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((listen_addr, listen_port))
    sock.settimeout(0.5)

    # Creating clients and messages variables
    clients = []
    messages = []

    # Dict with user names
    names = {}

    # Listen ports
    sock.listen(MAX_CONNECTIONS)
    # Main loop of server
    while True:
        try:
            conn, addr = sock.accept()
        except OSError:
            pass
        else:
            LOG.info(f"Connected with: {addr}")
            print(f"{addr} connected to the server!")
            clients.append(conn)
        
        # Created data variables
        recv_data = []
        write_data = []
        err_data = []

        # Search waiting clients
        try:
            if clients:
                recv_data, write_data, err_data = select.select(clients, clients, [], 0)
        except OSError:
            pass

        # get message, and if error excepting client
        if recv_data:
            for client_with_message in recv_data:
                try:
                    process_client_message(get_message(client_with_message), messages, client_with_message,
                                        clients, names)
                except Exception as err:
                    LOG.info(f'Client {client_with_message.getpeername()} '
                            f'disconnect from server. Error: {err}')
                    clients.remove(client_with_message)
                    
        # If there is the message, process everyone
        for i in messages:
            try:
                process_message(i, names, write_data)
            except Exception:
                LOG.info(f"Connection with user {i[DESTINATION]} was lost.")
                clients.remove(names[i[DESTINATION]])
                del names[i[DESTINATION]]
        messages.clear()
