import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import api
import tapes


def main():
    if os.path.isdir(tapes.CASSETTE_DIR):
        shutil.rmtree(tapes.CASSETTE_DIR)
    os.makedirs(tapes.CASSETTE_DIR)
    for path in api.seed():
        print("taped %-24s -> %s" % (path, tapes.slug(path) + ".yaml"))
    print("%d cassettes in %s" % (len(api.SEEDS), tapes.CASSETTE_DIR))


if __name__ == "__main__":
    main()
