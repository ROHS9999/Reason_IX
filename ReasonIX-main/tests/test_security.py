import pytest

import security


def test_blocks_non_http_schemes():
    for url in ("file:///etc/passwd", "ftp://example.com/x", "javascript:alert(1)"):
        with pytest.raises(ValueError):
            security.validate_url(url)


def test_blocks_private_and_loopback_addresses():
    for url in ("http://127.0.0.1/", "http://localhost:8000/", "http://169.254.169.254/latest/meta-data/",
                "http://10.0.0.5/", "http://192.168.1.1/"):
        with pytest.raises(ValueError):
            security.validate_url(url)
