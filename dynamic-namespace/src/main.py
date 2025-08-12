class DynamicNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)
    
    def __contains__(self, key):
        return hasattr(self, key)
    
    def merge(self, other):
        if isinstance(other, dict):
            self.__dict__.update(other)
        else:
            self.__dict__.update(other.__dict__)
        return self

config = DynamicNamespace(debug=True, port=8080)
config.merge({'host': 'localhost', 'ssl': False})
print(f"Debug: {config.debug}, Port: {config.port}")