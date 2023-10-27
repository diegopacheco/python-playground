import requests
cert_file_path = "cert.pem"
key_file_path = "key.pem"

url = "https://google.com.br/"
params = {"param_1": "value_1", "param_2": "value_2"}
cert = (cert_file_path, key_file_path)
r = requests.get(url, params=params, cert=cert)
print(r)