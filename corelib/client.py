import argparse
import json
from socket import *
import threading
import time
from corelib.common.utils import get_message, send_message
from corelib.common.variables import ACTION, ACCOUNT_NAME, DEFAULT_IP_ADDRESS, DEFAULT_PORT, DESTINATION, ERROR, EXIT, MESSAGE, MESSAGE_TEXT, PRESENCE, RESPONSE, SENDER, TIME, USER
from corelib.common.errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from corelib.metaclasses import ClientVerifier
import sys
import datetime
from logs.client_log_config import LOG
from corelib.common.decos import log


class ClientSender(threading.Thread, metaclass=ClientVerifier):

    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    @log
    def create_exit_message(self):
        """Message about exit."""
        time = datetime.datetime.now()
        return {
            ACTION: EXIT,
            TIME: time.isoformat(),
            ACCOUNT_NAME: self.account_name,
        }

    @log
    def create_message(self):
        """Function - create message for sending to server"""
        to_user = input("Input received user: ")
        msg = input("Input your message or !!! for exit.")
        time = datetime.datetime.now()
        msg_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.isoformat(),
            MESSAGE_TEXT: msg, 
        }
        LOG.debug(f"Created dict message: {msg_dict}")

        try:
            send_message(self.sock, msg_dict)
            LOG.info(f"Send message for user {to_user}")
        except:
            LOG.critical("Lost connection.")
            sys.exit(1)

    @staticmethod
    def print_help():
        """Function write documentation"""
        print('Commands:')
        print('message - send message. User and text will be requested later.')
        print('help - write help text')
        print('exit - exit from program')

    @log
    def user_interactive(self):
        """
        Function of interaction with user, take commands, send message.
        """
        self.print_help()
        while True:
            command = input("Input the command: ")
            if command == "message":
                self.create_message()
            elif command == "help":
                self.print_help()
            elif command == "exit":
                send_message(self.sock, self.create_exit_message())
                print("Close connection.")
                LOG.info("Close connection for user command.")
                time.sleep(1)
                break
            else:
                print("Incorrect command. Try 'help'.")


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    @log
    def message_from_server(self):
        """Function - received messages from another clients, sended to server"""
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                    print(f"\n Get message from client {message[SENDER]}:"
                        f"\n{message[MESSAGE_TEXT]}")
                    LOG.info(f"Get message from client {message[SENDER]}:"
                            f"\n{message[MESSAGE_TEXT]}")
                else:
                    LOG.error(f"Get incorrect message from server: {message}")
            except IncorrectDataRecivedError:
                LOG.error(f"Can't decode received message.")
            except (OSError, ConnectionError, ConnectionAbortedError):
                LOG.critical("Losing connection to the server.")
                break


@log
def arg_parser():
    """Парсер аргументов коммандной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_addr = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        LOG.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_addr, server_port, client_name


# @log
# def get_options(args, options_file):
#     '''
#     Get server options
#     :param args: Command line arguments
#     :param options_file: Options file name
#     :return: dict
#     '''
#     options = config.get_json_options(options_file)
#     cl_options = config.get_command_options(args, "a:p:n:")
#     for opt in cl_options:
#         if opt[0] == "-a":
#             options["DEFAULT"]["HOST"] = opt[1]
#         elif opt[0] == "-p":
#             options["DEFAULT"]["PORT"] = opt[1]
#         elif opt[0] == "-n":
#             options["DEFAULT"]["NAME"] = opt[1]

#     server_addr = options["DEFAULT"]["HOST"]
#     server_port = options["DEFAULT"]["PORT"]
#     client_name = options["DEFAULT"]["NAME"]

#     return server_addr, server_port, client_name


@log
def create_presence(account_name="Guest"):
    """
    Generating request about presence of client
    Args:
        account_name (str, optional): _description_. Defaults to "Guest".
    """
    time = datetime.datetime.now()
    out = {
        ACTION: PRESENCE,
        TIME: time.isoformat(),
        USER: {
            ACCOUNT_NAME: account_name,
        },
    }
    LOG.debug(f"Created presence message for client {account_name}")

    return out


@log
def process_response_ans(message):
    """
    Function received server answer of message about presence,
    return 200 if all ОК or generate exception as error
    """
    LOG.debug(f'Received message from server: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


def run():
    print("Console messager. Client module.")

    server_addr, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input("Input tour name: ")

    LOG.info(
        f'Start client with: server address: {server_addr}, '
        f'port: {server_port}, username: {client_name}.')
    
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((server_addr, server_port))
        send_message(sock, create_presence(client_name))
        answer = process_response_ans(get_message(sock))
        LOG.info(f"Connected to server with: server answer: {answer}")
        print("Connected to the server.")
    except json.JSONDecodeError:
        LOG.error("Failed unpack Json message")
        sys.exit(1)
    except ServerError as err:
        LOG.error(f"Failed, server error: {err}")
        sys.exit(1)
    except ReqFieldMissingError as err:
        LOG.error(f"In server answer missing mandated field: {err}")
        sys.exit(1)
    except ConnectionRefusedError as err:
        LOG.critical(f"Connection refused: {err}")
        sys.exit(1)
    else:
        # If connection to the server is correct,
        # start client service to received message.
        module_receiver = ClientReader(client_name, sock)
        module_receiver.daemon = True
        module_receiver.start()

        # start send message and interaction with users
        module_sender = ClientSender(client_name, sock)
        module_sender.daemon = True
        module_sender.start()
        LOG.debug("Starts process.")

        # main loop, if one of the process will be close,
        # it means or lost connection or user print 'exit'.
        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break
