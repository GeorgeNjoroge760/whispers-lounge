import re


class Validators:
    @staticmethod
    def not_empty(value, field_name="Field"):
        if not value or not str(value).strip():
            raise ValueError(f"{field_name} cannot be empty")

    @staticmethod
    def positive_number(value, field_name="Value", allow_zero=False):
        try:
            v = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a number")
        if v < 0 or (not allow_zero and v == 0):
            raise ValueError(f"{field_name} must be {'non-negative' if allow_zero else 'positive'}")

    @staticmethod
    def username(value):
        Validators.not_empty(value, "Username")
        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValueError("Username can only contain letters, numbers, and underscores")

    @staticmethod
    def password(value):
        Validators.not_empty(value, "Password")
        if len(value) < 4:
            raise ValueError("Password must be at least 4 characters")

    @staticmethod
    def email(value):
        if value and not re.match(r"^[^@]+@[^@]+\.[^@]+$", value):
            raise ValueError("Invalid email format")

    @staticmethod
    def integer(value, field_name="Value"):
        try:
            int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a whole number")
