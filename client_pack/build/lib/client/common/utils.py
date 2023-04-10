from common import jim
from common.variables import MAX_PACKAGE_LENGTH
from common.decos import log
from common.errors import IncorrectDataRecivedError, NonDictInputError


@log
def get_message(client):
    """
    Utile for get and decoding message get bites gives dict,
    if get something else gives error message.
    :param client:
    :return:
    """
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        response = jim.unpack(encoded_response)
        if isinstance(response, dict):
            return response
        else:
            raise IncorrectDataRecivedError
    else:
        raise IncorrectDataRecivedError
    

@log
def send_message(sock, message):
    """
    Utile encoding and send message
    get dict and send it.
    :param sock:
    :param message:
    :return:
    """
    if not isinstance(message, dict):
        raise NonDictInputError
    sock.send(jim.pack(message))
    
