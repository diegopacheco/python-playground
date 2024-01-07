class SecretData:
    def __init__(self):
        self.secret = "123456"

    def __getattribute__(self, key):
        print("Sorry! No funny business here! Key: " + str(key) + " not allowed")

sd = SecretData()
sd.secret = 10
print(sd.secret)

