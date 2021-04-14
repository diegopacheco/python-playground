import base64
from Crypto.Cipher import AES
from Crypto import Random
import os

BS = 32
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[:-ord(s[len(s)-1:])]

class AESCipher:
    def __init__( self, key ):
        self.key = key

    def encrypt( self, raw ):
        raw = pad(raw)
        iv = Random.new().read( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw ) ) 

    def decrypt( self, enc ):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[16:] ))


secret_key = os.urandom(32)
service = AESCipher(secret_key)

ciphertext = service.encrypt("this is a message")
print("Ciphertext: " + str(ciphertext))

plaintext = service.decrypt(ciphertext)
print("Plaintext: " + str(plaintext))