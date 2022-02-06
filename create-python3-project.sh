#!/bin/bash

mkdir src/
touch src/main.py

echo "print('Hello, world!')" > src/main.py
echo "numpy" > requirements.txt

echo "#!/bin/bash
pip install -r requirements.txt" > install-deps.sh
chmod +x install-deps.sh

touch run.sh
echo "#!/bin/bash

python3 src/main.py"
chmod +x run.sh
