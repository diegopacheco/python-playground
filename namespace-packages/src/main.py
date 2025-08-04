# Create virtual namespace
from types import SimpleNamespace

ns = SimpleNamespace()
ns.database = SimpleNamespace()
ns.database.host = 'localhost'
ns.database.port = 5432

print(ns.database.host)
print(ns.database.port)