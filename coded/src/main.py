import codecs

def reverse_encode(text, errors='strict'):
    return text[::-1].encode('utf-8'), len(text)

def reverse_decode(data, errors='strict'):
    if isinstance(data, memoryview):
        raw = data.tobytes()
        consumed = data.nbytes
    elif isinstance(data, (bytes, bytearray)):
        raw = bytes(data)
        consumed = len(data)
    else:
        text = str(data)
        return text[::-1], len(text)

    text = raw.decode('utf-8', errors)
    return text[::-1], consumed

class ReverseCodec(codecs.Codec):
    def encode(self, text, errors='strict'):
        return reverse_encode(text, errors)
    
    def decode(self, data, errors='strict'):
        return reverse_decode(data, errors)

def reverse_codec_search(name):
    if name == 'reverse':
        return codecs.CodecInfo(
            encode=reverse_encode,
            decode=reverse_decode,
            name='reverse'
        )

codecs.register(reverse_codec_search)
text = "Hello World"
encoded = text.encode('reverse')
print(encoded)
print(encoded.decode('reverse'))