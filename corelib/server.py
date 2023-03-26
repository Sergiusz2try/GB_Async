import argparse
import select
from socket import *
import sys
import threading
from corelib.common.utils import get_message, send_message
from corelib.common.variables import ACCOUNT_NAME, ACTION, DEFAULT_PORT, DESTINATION, ERROR, EXIT, MAX_CONNECTIONS, MESSAGE, MESSAGE_TEXT, PRESENCE, RESPONSE_200, RESPONSE_400, SENDER, TIME, USER
from corelib.descripts import Port
from corelib.metaclasses import ServerVerifier
from logs.server_log_config import LOG
from corelib.common.decos import log
from corelib.models.server import ServerStorage


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


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_addr, listen_port, database):
        self.listen_addr = listen_addr
        self.listen_port = listen_port
        self.clients = []
        self.database = database
        self.messages = []
        self.names = {}
        super().__init__()

    def init_sock(self):
        '''
        Run server
        :param args: Command line arguments
        :return:
        '''

        LOG.info(
            f'Start server, port for connection: {self.listen_port}, '
        )

        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind((self.listen_addr, self.listen_port))
        sock.settimeout(0.5)

        # Listen ports
        self.sock = sock
        self.sock.listen(MAX_CONNECTIONS)

    def run(self):
        self.init_sock()

        # Main loop of server
        while True:
            try:
                conn, addr = self.sock.accept()
            except OSError:
                pass
            else:
                LOG.info(f"Connected with: {addr}")
                print(f"{addr} connected to the server!")
                self.clients.append(conn)
            
            # Created data variables
            recv_data = []
            write_data = []
            err_data = []

            # Search waiting clients
            try:
                if self.clients:
                    recv_data, write_data, err_data = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # get message, and if error excepting client
            if recv_data:
                for client_with_message in recv_data:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except Exception as err:
                        LOG.info(f'Client {client_with_message.getpeername()} '
                                f'disconnect from server. Error: {err}')
                        self.clients.remove(client_with_message)
                        
            # If there is the message, process everyone
            for i in self.messages:
                try:
                    self.process_message(i, write_data)
                except Exception:
                    LOG.info(f"Connection with user {i[DESTINATION]} was lost.")
                    self.clients.remove(self.names[i[DESTINATION]])
                    del self.names[i[DESTINATION]]
            self.messages.clear()


    @log
    def process_client_message(self, message, client):
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
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = "Username already exist."
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # If it message add it to message list
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message and \
                SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        # If client exit.
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        # Else bad request.
        else:
            send_message(client, RESPONSE_400)
            return
        

    @log
    def process_message(self, message, listen_socks):
        """
        Function address sended message correct user. Get dict message,
        list registered users and listen sockets. Nothing return.
        :param message:
        :param names:
        :param listen_socks:
        :return:
        """
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            LOG.info(f"Sended message for user: {message[DESTINATION]}"
                    f"from user {message[SENDER]}")
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            LOG.error(f"User {message[DESTINATION]} are not registered on the server.")


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


def print_help():
    print('Commands:')
    print('users - list of users')
    print('connected - list of active users')
    print('loghist - list of users history')
    print('exit - close server.')
    print('help - help list')


def main():
    # Start server
    listen_addr, listen_port = arg_parser()

    database = ServerStorage()

    server = Server(listen_addr, listen_port, database)
    server.daemon = True
    server.start()

    print_help()

    # Основной цикл сервера:
    while True:
        command = input('Input command: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            break
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'User {user[0]}, last entering: {user[1]}')
        elif command == 'connected':
            for user in sorted(database.active_users_list()):
                print(f'User {user[0]}, connected: {user[1]}:{user[2]}, connection time: {user[3]}')
        elif command == 'loghist':
            name = input('Input username to see a history. To see all history, press Enter: ')
            for user in sorted(database.login_history(name)):
                print(f'User: {user[0]} entering time: {user[1]}. Online at: {user[2]}:{user[3]}')
        else:
            print('Incorrect command.')