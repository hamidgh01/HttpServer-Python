import socket

from app.logging import logger
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
        1: decode header_part bytes / split every line to a list
        2: parse request-line (first line of header-part) to extract
           <METHOD> <PATH> <VERSION> using 'HTTPParser._parse_request_line()'
        3: parse raw headers into a dict using 'HTTPParser._parse_headers()'
        4: read the rest of body if there is, via '_extract_body_from_buffer()'
        5: build 'HTTPRequest' object using extracted data in previous steps
        """

        try:
            header_text = header_part.decode("iso-8859-1")
        except Exception:
            logger.debug("Failed to decode header_part")
            raise ValueError("Invalid header encoding")

        header_lines = header_text.split("\r\n")
        if not header_lines:
            raise ValueError("Empty request-line")

        req_line = header_lines[0]
        try:
            method, path, version = HTTPParser._parse_request_line(req_line)
            headers = HTTPParser._parse_headers(header_lines[1:])
        except ValueError:
            raise

        body = b""
        content_length = headers.get("content-length", None)
        # If Content-Length present, read the rest of the body
        if content_length is not None:
            try:
                content_length = int(content_length)
                body = HTTPParser._extract_body_from_buffer(
                    start_of_body, content_length, connection
                )
            except ValueError:
                logger.warning(
                    "Invalid Content-Length value: %r", content_length
                )
                # should I raise it?
            except socket.timeout:
                raise

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
        Parse raw headers into a dict[str, str] with lower-cased header names.
        NOTE: Combine multiple header fields with the same name into a
              single comma-separated value (mentioned in related line)
        """
        headers = {}
        for raw in lines:
            if raw == "":
                continue
            if ":" not in raw:
                logger.debug("Skipping malformed header line: %r", raw)
                continue
            name, _, value = raw.partition(":")
            name = name.strip().lower()  # lower-cased header names
            value = value.strip()
            if name in headers:  # Noted in docstring
                headers[name] += f", {value}"
            else:
                headers[name] = value

        return headers

    @staticmethod
    def _extract_body_from_buffer(
        start_of_body: bytes, content_length: int, connection: socket.socket
    ) -> bytes:
        """ read the rest of body using 'connection.recv()' if there is """

        body = start_of_body or b""
        to_read = content_length - len(body)
        while to_read > 0:
            try:
                chunk = connection.recv(min(10240, to_read))  # 10 KB
            except socket.timeout:
                raise
            if not chunk:
                logger.debug("Client closed while sending body")
                break
            body += chunk
            to_read -= len(chunk)

        return body

    # @staticmethod
    # def _extract_body_chunks_from_buffer(connection: socket.socket) -> bytes:
    #     """ ... """
    #     body = b""
    #     ...
