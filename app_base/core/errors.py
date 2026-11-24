class DiddiShopError(Exception):
    """Base error that can be mapped to a stable API error."""


class ConflictError(DiddiShopError):
    pass


class NotConfiguredError(DiddiShopError):
    pass


class InvalidTransitionError(DiddiShopError):
    pass
