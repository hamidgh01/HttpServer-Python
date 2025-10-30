""" <HTTPResponse class> Represents and builds a simple HTTP-Response,
as follows:
+-----------------------------------------+
│ <version> <status-code> <reason-phrase> │ Status-Line
│ <key: value>                            │
│ <key: value>                            │ Headers
│ <key: value>                            │
│ ...                                     │
│                                         │ empty line
│ data:                                   │
│ cand be:                                │
│ - text/plain                            │ Body
│ - text/html                             │
│ - application/json                      │
│ etc.                                    │
+-----------------------------------------+
"""

from typing import Optional


default_response_body = b"""
<br>
<h1 style='text-align: center;'>
  I'm developing my own HTTPServer... :)))
</h1>
"""


class HTTPResponse:

    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[dict[str, str]] = None,
        body: bytes = default_response_body,
        mem_type: str = "text/html"
    ):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body
        self.mem_type = mem_type

    def build_response(self) -> bytes:
        """ Convert response-object into raw HTTP bytes.
        Build a simple HTTP/1.1 response with required headers:
        - Content-Length
        - Content-Type
        - Connection: close
        """

        body = self.body
        reason = self._get_reason_phrase()

        # Base headers
        headers = {
            "Server": "HTTPServer-by-hamidgh01/0.1",
            "Content-Length": str(len(body)),
            "Content-Type": f"{self.mem_type}; charset=utf-8",
            "Connection": "close",
            **self.headers,
        }

        status_line = f"HTTP/1.1 {self.status_code} {reason}\r\n"
        headers_line = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
        empty_line = "\r\n"

        return (status_line + headers_line + empty_line).encode("utf-8") + body

    def _get_reason_phrase(self) -> str:
        """Return standard reason phrase for given status."""
        phrases = {
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        }
        return phrases.get(self.status_code, "Unknown")
