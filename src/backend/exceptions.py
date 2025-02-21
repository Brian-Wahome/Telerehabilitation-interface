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
