import json
import sys
import getopt


def get_json_options(file):
    '''
    Get options from JSON file
    :param file: File name
    :return: dict
    '''
    try:
        with open(file, "r") as f:
            config = json.load(f)
    except ValueError as err:
        print(f"Can't read config file: {file}, with error: {err}")
        sys.exit(2)

    return config


def get_command_options(args, short_opts):
    '''
    Get options from command line
    :param args: Command line arguments
    :param short_opts:
    :return: 
    '''
    try:
        opts, _ = getopt.getopt(args[1:], short_opts)
    except getopt.GetoptError as err:
        print(f"Invalid argument. Error[{err}]")
        sys.exit(2)

    return opts