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
│ can be:                                 │
│ - text/plain                            │ Body
│ - text/html                             │
│ - application/json                      │
│ etc.                                    │
+-----------------------------------------+
"""

from typing import Optional, Callable
from datetime import datetime, timezone

from app.config import settings
from .status import STATUS_MESSAGES


class HTTPResponse:

    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[dict[str, str]] = None,
        body: bytes = b"",
        mem_type: Optional[str] = None,
        chunked: bool = False,
        iter_body: Optional[Callable[[], bytes]] = None,
        is_for_head_method: bool = False
    ):
        self.status_code: int = status_code
        self.headers: dict[str, str] = headers or {}
        self.body: bytes = body
        self.mem_type: Optional[str] = mem_type
        self.chunked: bool = chunked
        self.iter_body: Callable[[], bytes] = iter_body
        self.is_for_head_method: bool = is_for_head_method

    def build_response(self) -> bytes:
        """ builds and returns a simple HTTP/1.1 HttpResponse (in bytes)
        steps:
        1- build and initialize `headers` dict using self._base_headers()
        2- few changes in `headers` base on 'self.chunked' and 'self.iter_body'
        3- add provided headers for response (self.headers) to `headers` dict
        4- get Status-line / join `headers` into a string / add an empty-line
           -> concatenate them -> convert to 'bytes' -> "HttpHeader block"
        then:
        _ if HEAD method is requested -> return "HttpHeader block" (bytes)
        _ for chunked body transferring -> first send "HttpHeader" (bytes),
          then send body-chunks using 'self.iter_body'
        _ to build HttpResponse completely -> add Response-Body (self.body)
          to "HttpHeader" and build the whole HttpResponse and return
        """

        headers = self._base_headers()
        if self.chunked and self.iter_body:  # chunked transferring provided
            headers["transfer-encoding"] = "chunked"
            headers.pop("content-length", None)
        # add user headers:
        for k, v in self.headers.items():
            # don't overwrite headers provided by `self._base_headers()`
            if (key := k.lower()) not in headers:
                headers[key] = v

        status_line = self._status_line()
        headers_lines = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
        empty_line = "\r\n"
        http_header_block = status_line + headers_lines + empty_line
        http_header_block_bytes = http_header_block.encode("utf-8")

        if self.is_for_head_method or (self.chunked and self.iter_body):
            return http_header_block_bytes
            # when self.chunked is True and self.iter_body is provided:
            # we have "chunked body transferring" -> so:
            # send only Http-Header first / then stream body chunks

        if not self.chunked and self.body:
            return http_header_block_bytes + self.body
        else:
            raise ...  # ToDo: handle here later (Internal server error)

    def _status_line(self) -> str:
        """
        builds the first line of Http-Header (Status-Line) for HttpResponse.
        HttpResponse Status-Line schema: `<version> <status-code> <reason>`
        """
        message = STATUS_MESSAGES.get(self.status_code, "Unknown")
        return f"HTTP/1.1 {self.status_code} {message}\r\n"

    def _base_headers(self) -> dict[str, str]:
        """
        provides base (default) Headers for HttpResponse
        (doesn't add 'content-length' & 'content-type' headers if
        the Http-Response is preparing for HEAD method)
        """
        now_ = datetime.now(tz=timezone.utc)
        default_headers = {
            "date": now_.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "server": settings.PROJECT_NAME,
        }
        if not self.is_for_head_method:
            if not self.chunked and self.body:
                default_headers["content-length"] = str(len(self.body))
            if self.mem_type:
                default_headers["content-type"] = self.mem_type

        return default_headers
