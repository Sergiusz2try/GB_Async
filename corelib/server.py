import argparse
import select
from socket import *
import sys
from corelib.common.utils import get_message, send_message
from corelib.common.variables import ACCOUNT_NAME, ACTION, DEFAULT_PORT, DESTINATION, ERROR, EXIT, MAX_CONNECTIONS, MESSAGE, MESSAGE_TEXT, PRESENCE, RESPONSE_400, SENDER, TIME, USER
from corelib.descripts import Port
from corelib.metaclasses import ServerVerifier
from logs.server_log_config import LOG
from corelib.common.decos import log


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


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_addr, listen_port):
        self.listen_addr = listen_addr
        self.listen_port = listen_port
        self.clients = []
        self.messages = []
        self.names = {}

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
                        self.process_client_message(get_message(client_with_message), self.messages, client_with_message,
                                            self.clients, self.names)
                    except Exception as err:
                        LOG.info(f'Client {client_with_message.getpeername()} '
                                f'disconnect from server. Error: {err}')
                        self.clients.remove(client_with_message)
                        
            # If there is the message, process everyone
            for i in self.messages:
                try:
                    self.process_message(i, self.names, write_data)
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
                send_message(client, self.response_200())
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
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        # Else bad request.
        else:
            send_message(client, self.response_400())
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


    @log
    @staticmethod
    def response_200():
        msg = {
            "response": 200,
            "alert": "OK"
        }

        return msg


    @log
    @staticmethod
    def response_400():
        msg = {
            "response": 400,
            "alert": "Bad request"
        }

        return msg


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

def main():
    # Start server
    listen_addr, listen_port = arg_parser()

    server = Server(listen_addr, listen_port)
    server.run()