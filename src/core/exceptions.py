class LastAdminError(Exception):
    """
    Raised when an operation attempts to leave the system without administrators.

    This exception is triggered when attempting to demote the role or delete
    the account of the only user with the 'admin' role.
    """
    pass

class UselessOperationError(Exception):
    """
    Raised when a role change is attempted but the user already has that role.

    This prevents unnecessary database writes when the target role is identical 
    to the user's current role.
    """
    pass

