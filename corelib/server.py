import select
from socket import *
import time
from corelib import jim, config
from logs.server_log_config import LOG
from corelib.decos import log


def run(args, options_file):
    '''
    Run server
    :param args: Command line arguments
    :return:
    '''
    conf = get_options(args, options_file)
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((conf["DEFAULT"]["HOST"], conf["DEFAULT"]["PORT"]))
    sock.settimeout(0.5)

    LOG.info(
        f'Запущен сервер, порт для подключений: {conf["DEFAULT"]["PORT"]}, '
    )

    print("Create server...")
    sock.listen(5)
    print("Server listening...")

    # Creating clients and messages variables
    clients = []
    messages = []

    while True:
        try:
            conn, addr = sock.accept()
        except OSError:
            pass
        else:
            LOG.info(f"Connected with: {addr}")
            clients.append(conn)
        
        # Created data variables
        recv_data = []
        write_data = []
        err_data = []

        try:
            if clients:
                recv_data, write_data, err_data = select.select(clients, clients, [], 0)
        except OSError:
            pass

        if recv_data:
            for client_with_message in recv_data:
                try:
                    process_client_message(
                        jim.unpack(client_with_message.recv(1024)),
                        messages,
                        client_with_message
                        )
                except:
                    LOG.info(f'Client {client_with_message.getpeername()} '
                            f'disconnect from server.')
                    
        if messages and write_data:
            msg = {
                "action": "message",
                "sender": messages[0][0],
                "time": time.isoformat(),
                "mess_text": messages[0][1],
            }

            del messages[0]
            for writing_client in write_data:
                try:
                    writing_client.send(jim.pack(msg))
                except:
                    LOG.info(f'Client {client_with_message.getpeername()} '
                            f'disconnect from server.')
                    clients.remove(writing_client)


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
def process_client_message(message, messages_list, client):
    """
    Message handler from clients, accepts a dictionary - a message from the client,
    checks the correctness, sends a response dictionary to the client with the result of the reception.
    :param message:
    :param messages_list:
    :param client:
    :return:
    """

    LOG.debug(f"Received message from client: {message}")
    if "action" in message and message["action"] == "presence" and "time" in message \
            and "user" in message and message["user"]["account_name"] == "Guest":
        client.send(response_200())
        return
    elif "action" in message and message["action"] == "message" and \
            "time" in message and "mess_text" in message:
        messages_list.append(message["account_name"], message["text"])
    else:
        client.send(response_400())
        return


@log
def response_200():
    msg = {
        "response": 200,
        "alert": "OK"
    }

    return jim.pack(msg)


@log
def response_400():
    msg = {
        "response": 400,
        "alert": "Bad request"
    }

    return jim.pack(msg)