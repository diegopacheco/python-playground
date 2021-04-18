import pickledb

db = pickledb.load('test.db', False)
db.set('key', 'value')
print(db.get('key'))
db.dump()