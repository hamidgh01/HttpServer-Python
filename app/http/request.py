""" <HTTPRequest class> Represents a simple HTTP-Request,
as follows:
+---------------------------+
│ <method> <path> <version> │ Request-Line
│ <key: value>              │
│ <key: value>              │ Headers
│ <key: value>              │
│ ...                       │
│                           │ empty line
│ {                         │
│ "data": "content",        │ Body
│ ...                       │
│ }                         │
+---------------------------+
"""

from typing import Optional


class HTTPRequest:

    def __init__(
        self,
        method: str,
        path: str,
        version: str,
        headers: dict[str, str],
        body: Optional[bytes] = None
    ):
        self.method = method
        self.path = path
        self.version = version
        self.headers = headers
        self.body = body or b""

    def __repr__(self):
        return f"<HTTPRequest {self.method} {self.path} {self.version}>"
