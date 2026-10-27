"""URL safety. Without this, a user could submit http://localhost:8000/... or a cloud metadata address
(169.254.169.254) and make OUR server fetch internal resources for them (SSRF)."""
import ipaddress
import socket
from urllib.parse import urlparse


def validate_url(url: str) -> None:
    """Raise ValueError unless the url is http(s) and every address it resolves to is a public one."""
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("Only http(s) URLs are allowed")
    port = p.port or (443 if p.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(p.hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise ValueError("Host could not be resolved")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise ValueError("URL points to a private or internal address")
