import re;

data = """
<cpf>111.345.670.01</cpf>
<cpf>112.345.670.02</cpf>
<cpf>112.345.670.04</cpf>
"""

cleanup_data = re.sub(r"<cpf>.*?</cpf>","000.000.00.00",data)
print(cleanup_data)
