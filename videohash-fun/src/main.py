from videohash import VideoHash

hash1 = VideoHash(url="https://www.youtube.com/watch?v=PapBjpzRhnA", download_worst=False)
print(str(hash1))
print(str(hash1.hash_hex))
