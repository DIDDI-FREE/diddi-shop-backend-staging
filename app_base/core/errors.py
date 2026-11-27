class DiddiShopError(Exception):
    """Base error that can be mapped to a stable API error."""

    code = "SHOP_ERROR"
    status_code = 409

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.details = details


class ConflictError(DiddiShopError):
    code = "CONFLICT"


class NotFoundError(DiddiShopError):
    code = "NOT_FOUND"
    status_code = 404


class ValidationError(DiddiShopError):
    code = "VALIDATION_ERROR"
    status_code = 422


class InsufficientStockError(ValidationError):
    code = "INSUFFICIENT_STOCK"


class PaymentPhoneRequiredError(ValidationError):
    code = "PAYMENT_PHONE_REQUIRED"


class PaymentReturnRequiredError(ValidationError):
    code = "PAYMENT_RETURN_REQUIRED"


class PaymentReturnInvalidError(ValidationError):
    code = "PAYMENT_RETURN_INVALID"


class NotConfiguredError(DiddiShopError):
    code = "NOT_CONFIGURED"
    status_code = 503


class DeliveryQuoteUnavailableError(DiddiShopError):
    code = "DELIVERY_QUOTE_UNAVAILABLE"
    status_code = 502


class InvalidTransitionError(DiddiShopError):
    code = "INVALID_TRANSITION"


class OrderNotCancellableError(DiddiShopError):
    code = "ORDER_NOT_CANCELLABLE"


class DeliveryAlreadyPickedUpError(OrderNotCancellableError):
    code = "DELIVERY_ALREADY_PICKED_UP"


class ClaimWindowExpiredError(DiddiShopError):
    code = "CLAIM_WINDOW_EXPIRED"


class ClaimAlreadyOpenError(DiddiShopError):
    code = "CLAIM_ALREADY_OPEN"
