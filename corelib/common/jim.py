import json


def pack(dict_msg):
    '''
    Создает объект JSON для отправки через TCP
    :param dict_msg: Dict
    :return: str
    '''
    str_msg = json.dumps(dict_msg)

    return str_msg.encode("utf-8")


def unpack(bt_str):
    '''
    Распаковка полученного сообщения
    :param bt_str: bit str
    :return: dict
    '''
    str_decoded = bt_str.decode("utf-8")

    return json.loads(str_decoded)