class BankError(Exception):
    status = 400


class ValidationError(BankError):
    status = 422


class NotFound(BankError):
    status = 404


class InsufficientFunds(BankError):
    status = 409


class DuplicateEmail(BankError):
    status = 409
