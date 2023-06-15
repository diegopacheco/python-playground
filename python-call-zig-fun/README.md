### Build Zig Lib
```bash
zig build-lib add.zig -dynamic
```

### Run
```bash
export LD_LIBRARY_PATH=./
python app.py
```
will output
```bash
python3 app.py
Zig result is 1 + 2 == 3
```