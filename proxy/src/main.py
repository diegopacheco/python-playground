class ModuleProxy:
    def __init__(self, module_name):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name):
        if self._module is None:
            self._module = __import__(self.module_name)
        attr = getattr(self._module, name)
        print(f"Accessing {self.module_name}.{name}")
        return attr

math_proxy = ModuleProxy('math')
print(math_proxy.pi)
print(math_proxy.sqrt(16))