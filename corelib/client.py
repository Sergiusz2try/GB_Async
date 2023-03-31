import argparse
import json
from socket import *
import threading
import time
from corelib.common.utils import get_message, send_message
from corelib.common.variables import *
from corelib.common.errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from corelib.metaclasses import ClientVerifier
import sys
import datetime
from corelib.models.client_db import ClientDatabase
from logs.client_log_config import LOG
from corelib.common.decos import log


sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientVerifier):

    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
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

        with database_lock():
            if not self.database.check_user(to_user):
                LOG.error(f"Trying send message to unexistent user: {to_user}")
                return

        time = datetime.datetime.now()
        msg_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.isoformat(),
            MESSAGE_TEXT: msg, 
        }
        LOG.debug(f"Created dict message: {msg_dict}")

        with sock_lock:
            try:
                send_message(self.sock, msg_dict)
                LOG.info(f"Send message for user {to_user}")
            except OSError as err:
                if err.errno:
                    LOG.critical("Lost connection.")
                    sys.exit(1)
                else:
                    LOG.error("Can't send message. Time out.")

    @staticmethod
    def print_help():
        """Function write documentation"""
        print('Commands:')
        print('message - send message. User and text will be requested later.')
        print('help - write help text')
        print('exit - exit from program')
        print("contacts - contacts list")
        print("edit - edit contacts list")
        print("history - history of message")

    def print_history(self):
        ask = input('Show income message - in, outcome - out, all - just Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nMessage from user: {message[0]} from {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\Message to user: {message[1]} from {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\Message from user: {message[0]}, to {message[1]} from {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input("To delete input 'del', to add input 'add': ")
        if ans == 'del':
            edit = input('Input username to delete: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    LOG.error('Trying delete unexistent user.')
        elif ans == 'add':
            edit = input('Input username to add: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock , self.account_name, edit)
                    except ServerError:
                        LOG.error("Can't send message to server.")

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
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except:
                        pass
                    print("Close connection.")
                    LOG.info("Close connection for user command.")
                time.sleep(1)
                break

            elif command == "contacts":
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == "edit":
                self.edit_contacts()

            elif command == "history":
                self.print_history()

            else:
                print("Incorrect command. Try 'help'.")


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    @log
    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    msg = get_message(self.sock)
                except IncorrectDataRecivedError:
                    LOG.error("Can't decode message.")
                except OSError as err:
                    if err.errno:
                        LOG.critical(f"Lost connection with server. Error: {err}")
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError,
                        json.JSONDecodeError):
                    LOG.critical("Lost connection with server")
                    break
                else:
                    if ACTION in msg and msg[ACTION] == MESSAGE and SENDER in msg and \
                        DESTINATION in msg and MESSAGE_TEXT in msg and msg[DESTINATION] \
                        == self.account_name:
                        print(f"Get message from user: {msg[SENDER]}:\n{msg[MESSAGE_TEXT]}")
                        with database_lock:
                            try:
                                self.database.save_message(msg[SENDER], self.account_name, msg[MESSAGE_TEXT])
                            except:
                                LOG.error("Error saving message")
                        LOG.info(f"Get message from user: {msg[SENDER]}:\n{msg[MESSAGE_TEXT]}")
                    else:
                        LOG.error(f"Get incorrect message from server: {msg}")

    # @log
    # def message_from_server(self):
    #     """Function - received messages from another clients, sended to server"""
    #     while True:
    #         try:
    #             message = get_message(self.sock)
    #             if ACTION in message and message[ACTION] == MESSAGE and \
    #                     SENDER in message and DESTINATION in message \
    #                     and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
    #                 print(f"\n Get message from client {message[SENDER]}:"
    #                     f"\n{message[MESSAGE_TEXT]}")
    #                 LOG.info(f"Get message from client {message[SENDER]}:"
    #                         f"\n{message[MESSAGE_TEXT]}")
    #             else:
    #                 LOG.error(f"Get incorrect message from server: {message}")
    #         except IncorrectDataRecivedError:
    #             LOG.error(f"Can't decode received message.")
    #         except (OSError, ConnectionError, ConnectionAbortedError):
    #             LOG.critical("Losing connection to the server.")
    #             break


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


@log
def contacts_list_request(sock, name):
    LOG.debug(f'Requests contacts list to user {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    LOG.debug(f'Formed request {req}')
    send_message(sock, req)
    ans = get_message(sock)
    LOG.debug(f'Get answer {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


@log
def add_contact(sock, username, contact):
    LOG.debug(f'Creating contact {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Error creating contact')
    print('Successfully created contact.')


@log
def user_list_request(sock, username):
    LOG.debug(f'Request all known users {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


@log
def remove_contact(sock, username, contact):
    LOG.debug(f'Removing contact {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Error removing')
    print('Successfully removed')


@log
def database_load(sock, database, username):
    # Load list of known users
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        LOG.error('Error request of known users.')
    else:
        database.add_users(users_list)

    # Load contact list
    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        LOG.error('Error request contacts list.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


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

        sock.settimeout(1)

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
        # Initial DB
        database = ClientDatabase(client_name)
        database_load(sock, database, client_name)

        # If connection to the server is correct,
        # start client service to received message.
        module_receiver = ClientReader(client_name, sock)
        module_receiver.daemon = True
        module_receiver.start()
        LOG.debug("Start process")

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
