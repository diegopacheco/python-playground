class MetadataManagerSingleton:
    _instance = None
    metadata = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetadataManagerSingleton, cls).__new__(cls)
        return cls._instance

    def add_metadata(self, class_name, fields):
        self.metadata[class_name] = fields

    def get_metadata(self,class_name):
        return self.metadata.get(class_name, [])

def Sensitive(*sensitive_fields):
    """
    A class decorator that marks specified fields of a class as 'Sensitive',
    indicating these fields should be handled with care, possibly
    for security or privacy reasons.

    Args:
    *sensitive_fields (str): Fields within the class to be marked as sensitive.
    """
    def decorator(cls):
        MetadataManagerSingleton().add_metadata(cls.__name__, sensitive_fields)
        return cls
    return decorator

@Sensitive("name", "email")
class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
        self.anwser = "42"
    
    def __str__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email})"

class UserManager:
    def __init__(self):
        self.users = []

    def add_user(self, user):
        self.users.append(user)

    def print_users(self):
        for user in self.users:
            sensitive_fields = MetadataManagerSingleton().get_metadata(user.__class__.__name__)
            fields_to_print = {field: getattr(user, field, None) for field in vars(user) if field not in sensitive_fields}
            print(f"{user.__class__.__name__} with non-sensitive data: {fields_to_print}")
            
user_manager = UserManager()
user = User(1, "John Doe","jd@jd.jd")
user_manager.add_user(user)
user_manager.print_users()