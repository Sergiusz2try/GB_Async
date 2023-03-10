import json
from socket import *
import time
from corelib.errors import ReqFieldMissingError, ServerError
from corelib.user import User
import sys
import datetime
from corelib import jim, config
from logs.client_log_config import LOG
from corelib.decos import log


def run(args, options_file):
    conf = get_options(args, options_file)

    LOG.info(
        f'Start client with: server address: {conf["DEFAULT"]["HOST"]}, '
        f'port: {conf["DEFAULT"]["PORT"]}')
    
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect(conf["DEFAULT"]["HOST"], conf["DEFAULT"]["PORT"])
        sock.sendall(jim.pack(create_presence()))
        answer = process_response_ans(jim.unpack(sock.recv(1024)))
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
        client_mode = input("Input your mode ('send' or 'listen'): ")

        if client_mode == "send":
            try:
                sock.send(jim.pack(create_message(sock)))
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                LOG.error(f"Connection with server failed")
                sys.exit(1)

        if client_mode == 'listen':
                try:
                    message_from_server(jim.unpack(sock.recv(1024)))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    LOG.error(f'Connection with server was lose.')
                    sys.exit(1)




@log
def get_options(args, options_file):
    '''
    Get server options
    :param args: Command line arguments
    :param options_file: Options file name
    :return: dict
    '''
    options = config.get_json_options(options_file)
    cl_options = config.get_command_options(args, "a:p:")
    for opt in cl_options:
        if opt[0] == "-a":
            options["DEFAULT"]["HOST"] = opt[1]
        elif opt[0] == "-p":
            options["DEFAULT"]["PORT"] = opt[1]

    return options


@log
def message_from_server(message):
    """Function - received messages from another clients, sended to server"""
    if "action" in message and message["action"] == "message" and \
            "sender" in message and "mess_text" in message:
        print(f'Received message from client '
            f'{message["sender"]}:\n{message["mess_text"]}')
        LOG.info(f'Received message from client '
                    f'{message["sender"]}:\n{message["mess_text"]}')
    else:
        LOG.error(f'Received incorrect message from server: {message}')


@log
def create_message(sock, account_name="Guest"):
    """Function - create message for sending to server"""
    msg = input("Input your message or !!! for exit.")

    if msg == "!!!":
        sock.close()
        LOG.info("Exit at the client's command.")
        print("Thank's, goodbye!")
        sys.exit(0)
    
    msg_dict = {
        "action": "message",
        "time": time.isoformat(),
        "account_name": account_name,
        "mess_text": msg, 
    }
    LOG.debug(f"Created dict message: {msg_dict}")

    return msg_dict


@log
def create_presence(account_name="Guest"):
    """
    Generating request about presence of client
    Args:
        account_name (str, optional): _description_. Defaults to "Guest".
    """
    out = {
        "action": "presence",
        "time": time.isoformat(),
        "user": {
            "account_name": account_name,
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
    if "response" in message:
        if message["response"] == 200:
            return '200 : OK'
        elif message["response"] == 400:
            raise ServerError(f'400 : {message["error"]}')
    raise ReqFieldMissingError("response")


@log
def get_user():
    return User("User", "Password")


@log
def auth():
    user = get_user()
    time = datetime.datetime.now()
    msg = {
        "action": "authenticate",
        "time": time.isoformat(),
        "user": {
            "account_name": user.name,
            "password": user.password,
        },
    }

    return jim.pack(msg)
