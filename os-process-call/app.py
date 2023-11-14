import subprocess

result = subprocess.run(["ls", "-lsa"], capture_output=True, text=True)
print(result.stdout)