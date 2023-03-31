import argparse
import configparser
import os
import select
from socket import *
import sys
import threading
from corelib.common.utils import get_message, send_message
from corelib.common.variables import *
from corelib.descripts import Port
from corelib.metaclasses import ServerVerifier
from logs.server_log_config import LOG
from corelib.common.decos import log
from corelib.models.server_db import ServerStorage
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer
from corelib.server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt6.QtGui import QStandardItemModel, QStandardItem


new_connection = False
conflag_lock = threading.Lock()


@log
def arg_parser(default_port=7777, default_address="127.0.0.1"):
    """Парсер аргументов коммандной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
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
            except OSError as err:
                LOG.error(f"Error working with sockets: {err}")

            # get message, and if error excepting client
            if recv_data:
                for client_with_message in recv_data:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except (OSError) as err:
                        LOG.info(f'Client {client_with_message.getpeername()} '
                                f'disconnect from server. Error: {err}')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)
                        
            # If there is the message, process everyone
            for i in self.messages:
                try:
                    self.process_message(i, write_data)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError,
                        ConnectionRefusedError):
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
        global new_connection
        LOG.debug(f"Received message from client: {message}")

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
                and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
                with conflag_lock:
                    new_connection = True
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
            self.database.process_message(message[SENDER], message[DESTINATION])
            return
        
        # If client exit.
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message and \
                self.names[message[ACCOUNT_NAME]] == client:
            self.database.user_logout(message[ACCOUNT_NAME])
            LOG.info(f"Client {message[ACCOUNT_NAME]} correctly disconnect from the server.")
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return
        
        # If requests contact list
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)
        
        # If it's add contact
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message \
                and USER in message and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # If it's deleting contact
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message \
                and USER in message and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # If it's requests known users
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                    for user in self.database.users_list()]
            send_message(client, response)
        # Else bad request.
        else:
            response = RESPONSE_400
            response[ERROR] = "Incorrect request!"
            send_message(client, response)
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


def main():
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    
    listen_addr, listen_port = arg_parser()

    database = ServerStorage("server_base.sqlite")

    # Start server
    server = Server(listen_addr, listen_port, database)
    server.daemon = True
    server.start()

    # Create graph env to server
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Initial params the window
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Function to update connection list
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Function creating window with static client
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Function creating window with server settings
    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Function save settings
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')
                
    # Timer
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec()