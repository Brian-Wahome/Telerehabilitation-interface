class AppExceptions(Exception):
    """
    Base class for app exceptions
    """
    pass


class UserAlreadyExists(AppExceptions):
    """
    Exception raised on attempt to create a new user
    with information that already exists
    """
    pass


class MQTTClientNotFound(AppExceptions):
    """
    Exception raised on attempt to disconnect, delete or retrieve
    a mqtt client that no longer exists.
    """


class UserDoesNotExist(AppExceptions):
    """
    Exception raised on attempt to perform any action
    for a user that does not exist.
    """
