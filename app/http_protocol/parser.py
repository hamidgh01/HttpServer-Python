import socket

from app.config.logging import logger
from .request import HTTPRequest


class HTTPParser:
    """ Parse Http-Request and create a HTTPRequest object"""

    @staticmethod
    def parse_http_request(
        header_part: bytes, start_of_body: bytes, connection: socket.socket
    ) -> HTTPRequest:
        """
        Parse raw HTTP request bytes into a 'HTTPRequest' object

        steps:
        1: parse request-line (first line of header-part) to extract
           <METHOD> <PATH> <VERSION> using 'HTTPParser._parse_request_line()'
        2: parse raw headers into a dict using 'HTTPParser._parse_headers()'
        3: read the rest of body using 'connection.recv()' if there is
        4: build 'HTTPRequest' object using extracted data in previous steps
        """

        header_lines = header_part.decode("iso-8859-1").split("\r\n")
        req_line = header_lines[0]
        try:
            method, path, version = HTTPParser._parse_request_line(req_line)
            headers = HTTPParser._parse_headers(header_lines[1:])
        except ValueError as err:
            raise err

        body = start_of_body
        content_length = headers.get("content-length", None)
        try:
            length = int(content_length) if content_length is not None else None
            if length:
                # If Content-Length present, read the rest of the body
                to_read = length - len(body)
                while to_read > 0:
                    chunk = connection.recv(min(10240, to_read))  # 10 KB
                    if not chunk:
                        logger.debug("Client closed while sending body")
                        break
                    body += chunk
                    to_read -= len(chunk)
        except ValueError:
            logger.warning("Invalid Content-Length value: %r", content_length)

        return HTTPRequest(method, path, version, headers, body)

    @staticmethod
    def _parse_request_line(request_line: str) -> tuple[str, str, str]:
        """Parse <METHOD> <PATH> <VERSION> from request line"""
        parts = request_line.strip().split()
        if len(parts) != 3:
            raise ValueError(f"Malformed request line: {request_line!r}")
        return parts[0], parts[1], parts[2]

    @staticmethod
    def _parse_headers(lines: list[str]) -> dict[str, str]:
        """
        Parse raw headers (CRLF-separated) into a dict with
        lower-cased header names.
        Does not support multi-line folded headers (obsolete).
        """
        headers = {}
        for line in lines:
            if not line.strip():
                continue
            if ":" not in line:
                logger.debug("Skipping malformed header line: %r", line)
                continue
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()

        return headers
