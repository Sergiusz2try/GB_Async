from socket import *
from corelib import jim, config


def run(args, options_file):
    '''
    Run server
    :param args: Command line arguments
    :return:
    '''
    conf = get_options(args, options_file)
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((conf["DEFAULT"]["HOST"], conf["DEFAULT"]["PORT"]))
    print("Create server...")
    sock.listen(5)
    print("Server listening...")

    while True:
        conn, _ = sock.accept()
        conn.settimeout(5)
        with conn:
            while True:
                try:
                    msg = conn.recv(1024)
                    print(jim.unpack(msg))
                    conn.sendall(response_200())
                except error as err:
                    print(f"Error: {err}")
                    break
                if not msg:
                    break
        break

    sock.close()
    print("Server close...")


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


def response_200():
    msg = {
        "response": 200,
        "alert": "OK"
    }

    return jim.pack(msg)