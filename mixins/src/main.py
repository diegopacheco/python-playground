class LoggerMixin:
    """Mixin to add logging functionality to any class"""
    
    def log(self, message):
        print(f"[{self.__class__.__name__}] {message}")


class TimestampMixin:
    """Mixin to add timestamp functionality to any class"""
    
    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def log_with_timestamp(self, message):
        timestamp = self.get_timestamp()
        print(f"[{timestamp}] {message}")


class User(LoggerMixin, TimestampMixin):
    """User class that inherits from multiple mixins"""
    
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def create_account(self):
        self.log(f"Creating account for {self.name}")
        self.log_with_timestamp(f"Account created for {self.email}")
        return f"Account created for {self.name}"


class Product(LoggerMixin):
    """Product class that uses only the LoggerMixin"""
    
    def __init__(self, name, price):
        self.name = name
        self.price = price
    
    def update_price(self, new_price):
        old_price = self.price
        self.price = new_price
        self.log(f"Price updated from ${old_price} to ${new_price}")


if __name__ == "__main__":
    user = User("John Doe", "john@example.com")
    user.create_account()
    print()
    
    product = Product("Laptop", 999.99)
    product.update_price(899.99)
    print()
    
    user.log("This is a direct log message")
    user.log_with_timestamp("This message has a timestamp")