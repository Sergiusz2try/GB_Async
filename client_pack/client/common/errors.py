"""Errors"""


class IncorrectDataRecivedError(Exception):
    """Exception  - incorrect data received from socket"""
    def __str__(self):
        return 'Take incorrect message from another client.'


class ServerError(Exception):
    """Exception - server error"""
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class NonDictInputError(Exception):
    """Exception - args function a not dict"""
    def __str__(self):
        return 'Arg of function maybe dict.'


class ReqFieldMissingError(Exception):
    """Error - missing mandatory field in received dict"""
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'In received dict missing mandatory field {self.missing_field}.'