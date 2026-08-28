import re
from uuid import uuid4

from .errors import ValidationError

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def parse_name(raw):
    name = str(raw or "").strip()
    if len(name) < 2:
        raise ValidationError("full name must have at least 2 characters")
    if len(name) > 80:
        raise ValidationError("full name must not exceed 80 characters")
    return name


def parse_email(raw):
    email = str(raw or "").strip().lower()
    if not EMAIL.match(email):
        raise ValidationError(f"email '{email}' is not valid")
    return email


def new_account_number():
    return uuid4().hex[:12].upper()
