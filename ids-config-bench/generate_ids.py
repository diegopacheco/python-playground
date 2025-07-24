import json
import uuid

ids = [str(uuid.uuid4()) for _ in range(10000)]
with open('config/ids.json', 'w') as f:
    json.dump(ids, f)