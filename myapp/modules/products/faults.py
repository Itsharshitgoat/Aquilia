"""
Products module faults (error handling).

Faults define domain-specific errors and their recovery strategies.
They are automatically registered with the fault handling system.
"""

from aquilia.faults import Fault, FaultDomain, Severity, RecoveryStrategy


# Define fault domain for this module
PRODUCTS = FaultDomain.custom(
    "PRODUCTS",
    "Products module faults",
)


class ProductsNotFoundFault(Fault):
    """
    Raised when a product is not found.

    Recovery: Return 404 response
    """

    domain = PRODUCTS
    severity = Severity.INFO
    code = "PRODUCTS_NOT_FOUND"

    def __init__(self, item_id: int):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Product with id {item_id} not found",
            metadata={"item_id": item_id},
            retryable=False,
        )


class ProductsValidationFault(Fault):
    """
    Raised when product data validation fails.

    Recovery: Return 400 response with validation errors
    """

    domain = PRODUCTS
    severity = Severity.INFO
    code = "PRODUCTS_VALIDATION_ERROR"

    def __init__(self, errors: dict):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message="Validation failed",
            metadata={"errors": errors},
            retryable=False,
        )


class ProductsOperationFault(Fault):
    """
    Raised when a product operation fails.

    Recovery: Retry with exponential backoff
    """

    domain = PRODUCTS
    severity = Severity.WARN
    code = "PRODUCTS_OPERATION_FAILED"

    def __init__(self, operation: str, reason: str):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Operation '{operation}' failed: {reason}",
            metadata={"operation": operation, "reason": reason},
            retryable=True,
        )