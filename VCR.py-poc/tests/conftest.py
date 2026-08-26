import os
import sys
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

import api
import server
import tapes


@pytest.fixture
def cassettes(tmp_path, monkeypatch):
    monkeypatch.setattr(tapes, "CASSETTE_DIR", str(tmp_path / "tapes"))
    monkeypatch.setattr(tapes.RECORDER, "cassette_library_dir", str(tmp_path / "tapes"))
    monkeypatch.setattr(api, "IMAGE_DIR", str(tmp_path / "images"))
    os.makedirs(tapes.CASSETTE_DIR)
    os.makedirs(api.IMAGE_DIR)
    api.seed()
    return tmp_path / "tapes"


@pytest.fixture
def site(cassettes):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Player)
    Thread(target=httpd.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d" % httpd.server_address[1]
    httpd.shutdown()
