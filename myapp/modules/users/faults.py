"""
Users module faults (error handling).

Faults define domain-specific errors and their recovery strategies.
They are automatically registered with the fault handling system.
"""

from aquilia.faults import Fault, FaultDomain, Severity, RecoveryStrategy


# Define fault domain for this module
USERS = FaultDomain.custom(
    "USERS",
    "Users module faults",
)


class UsersNotFoundFault(Fault):
    """
    Raised when a user is not found.

    Recovery: Return 404 response
    """

    domain = USERS
    severity = Severity.INFO
    code = "USERS_NOT_FOUND"

    def __init__(self, item_id: int):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"User with id {item_id} not found",
            metadata={"item_id": item_id},
            retryable=False,
        )


class UsersValidationFault(Fault):
    """
    Raised when user data validation fails.

    Recovery: Return 400 response with validation errors
    """

    domain = USERS
    severity = Severity.INFO
    code = "USERS_VALIDATION_ERROR"

    def __init__(self, errors: dict):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message="Validation failed",
            metadata={"errors": errors},
            retryable=False,
        )


class UsersOperationFault(Fault):
    """
    Raised when a user operation fails.

    Recovery: Retry with exponential backoff
    """

    domain = USERS
    severity = Severity.WARN
    code = "USERS_OPERATION_FAILED"

    def __init__(self, operation: str, reason: str):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Operation '{operation}' failed: {reason}",
            metadata={"operation": operation, "reason": reason},
            retryable=True,
        )