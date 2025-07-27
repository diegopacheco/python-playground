class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            print(f"Getting new instance of {cls.__name__}")
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class UserDAO(metaclass=SingletonMeta):
    pass

dao1 = UserDAO()
dao2 = UserDAO()
dao3 = UserDAO()
dao4 = UserDAO()
print(dao1 is dao2)
print(dao3 is dao4)