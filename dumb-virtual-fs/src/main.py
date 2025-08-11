class VirtualFileSystem:
    def __init__(self):
        self._files = {}
    
    def create_file(self, path, content=""):
        self._files[path] = content
    
    def read_file(self, path):
        return self._files.get(path, "")
    
    def write_file(self, path, content):
        self._files[path] = content
    
    def list_files(self):
        return list(self._files.keys())
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self._files.clear()

with VirtualFileSystem() as vfs:
    vfs.create_file('/home/user/document.txt', 'Hello World')
    vfs.create_file('/home/user/data.json', '{"key": "value"}')
    print(vfs.list_files())
    print(vfs.read_file('/home/user/document.txt'))