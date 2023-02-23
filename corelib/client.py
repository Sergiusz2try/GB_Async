from socket import *
from corelib.user import User
import sys
import datetime
from corelib import jim, config


def run(args, options_file):
    conf = get_options(args, options_file)
    try:
        sock = create_connection((conf["DEFAULT"]["HOST"], conf["DEFAULT"]["PORT"]), 5)
    except error as err:
        print(f"Connection error: {err}")
        sys.exit(2)
    print("Create socket connection...")

    try:
        msg = auth()
        sock.sendall(msg)
        print("Send message...")
    except error as err:
        print(f"Send data error: {err}")

    while True:
        try:
            msg = sock.recv(1024)
            print(jim.unpack(msg))
        except error as err:
            print(f"Server error: {err}")
            break
        if not msg:
            break

    sock.close()
    print("Client close...")


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


def get_user():
    return User("User", "Password")


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