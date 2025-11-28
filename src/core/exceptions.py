# --- EXCEPTIONS FOR USERS ---
class LastAdminError(Exception):
    """
    Raised when an attempt is made to perform an action (e.g., demote, delete)
    on the only remaining user with administrator privileges in the system.
    """

    def __init__(self, username: str, action: str):
        self.username = username
        self.action = action
        super().__init__(
            f"Cannot {action} user '{username}': this is the last administrator."
        )


class UselessOperationError(Exception):
    """
    Raised when an attempt is made to assign a role to a user who already
    possesses that role, making the operation redundant.
    """

    def __init__(self, username: str):
        self.username = username
        super().__init__(f"User: {username}, already has this role")


class UsernameAlreadyExistsError(Exception):
    """
    Raised when attempting to create a user with a username that already exists in the system.
    """

    def __init__(self, username: str):
        self.username = username
        super().__init__(f"User with username '{username}' already exists.")


class UserHasOrdersError(Exception):
    """
    Raised when attempting to delete a user who has existing orders in the system.
    """

    def __init__(self, username: str):
        self.username = username
        super().__init__(
            f"Cannot delete user '{username}' because they have existing orders."
        )


# --- EXCEPTIONS FOR PRODUCTS ---
class ProductNameAlreadyExistsError(Exception):
    """
    Raised when attempting to create a new product with a name that is
    already in use by another existing product.
    """

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"A product with the name '{name}' already exists.")


class ProductInUseError(Exception):
    """
    Raised when attempting to delete a product that is referenced or
    included in an existing order.
    """

    def __init__(self, product_name: str):
        self.product_name = product_name
        super().__init__(
            f"Cannot delete product '{product_name}' because it is part of an existing order."
        )


class ProductUnavailableError(Exception):
    """
    Raised when an attempt is made to purchase a product that is currently unavailable.
    """

    def __init__(self, product_name: str):
        self.product_name = product_name
        super().__init__(
            f"Product '{product_name}' is currently unavailable for purchase."
        )


# --- EXCEPTIONS FOR ORDERS ---
class ProductNotFound(Exception):
    """Raised when a product ID in an order does not exist in the database."""

    def __init__(self, product_id: int):
        self.product_id = product_id
        super().__init__(f"Product with ID {product_id} not found.")


class InsufficientStock(Exception):
    """Raised when a product in an order does not have enough available stock for the requested quantity."""

    def __init__(
        self, product_id: int, product_name: str, requested: int, available: int
    ):
        self.product_id = product_id
        self.product_name = product_name
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product '{product_name}' (ID: {product_id}). "
            f"Requested: {requested}, Available: {available}."
        )


class EmptyOrder(Exception):
    """Raised when an attempt is made to create an order with no items."""

    def __init__(self, message: str = "Cannot create an order with no items.") -> None:
        self.message = message
        super().__init__(self.message)
