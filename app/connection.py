import socket

from app.config.logging import logger
from app.http_protocol.parser import HTTPParser
from app.http_protocol.response import HTTPResponse


class ConnectionHandler:
    """Handle a single client connection lifecycle."""

    def __init__(self, connection: socket.socket, address):
        self.conn = connection
        self.addr = address
        self.buffer = b""

    def handle_connection(self):
        """
        Main connection loop to handle http-requests-response cycle
        (single request per connection)
        how it works (generally):
            step_1: extract Request-Headers through 'self.read_until...' method
            step_2: parse Http-Request using 'HTTPParser' class
            step_3: build Http-Response using 'HTTPResponse' class
            step_4: send generated Http-Response through 'self.conn.sendall()'
        """

        header_part, remaining = self.read_until_body_and_header_terminator()

        if not header_part:
            logger.info("[-] Empty request from '%s:%d'", *self.addr)
            response_obj = HTTPResponse(
                status_code=400,
                body=b"Bad Request",
                mem_type="text/plain"
            )
            http_response = response_obj.build_response()
            self.conn.sendall(http_response)
            self.conn.close()
            return

        try:
            request = HTTPParser.parse_http_request(
                header_part=header_part,
                start_of_body=remaining,
                connection=self.conn
            )
            logger.info(
                "%s %s %s (from: %s:%d)",
                request.method,
                request.path,
                request.version,
                *self.addr
            )
            response_obj = HTTPResponse()
        except Exception as err:
            logger.info(f"[!] Failed to parse request: {err}")
            response_obj = HTTPResponse(
                status_code=400,
                body=b"Bad Request",
                mem_type="text/plain"
            )

        http_response = response_obj.build_response()
        self.conn.sendall(http_response)
        self.conn.close()

    def read_until_body_and_header_terminator(self):
        """
        Read from socket until the terminator is found.
        This uses a buffer and may read more bytes than strictly necessary;
        the extra bytes are returned as 'remaining' so caller can process them.

        Returns a tuple (header_part, remaining).
            header_part: data before terminator
            remaining: remaining bytes after terminator on buffer (starting
                       bytes of body)
        """

        terminator = b"\r\n\r\n"

        while True:
            chunk = self.conn.recv(10240)  # 10 KB
            if not chunk:
                logger.debug(
                    "socket closed by peer while waiting for terminator"
                )
                break
            self.buffer += chunk
            idx = self.buffer.find(terminator)  # Returns -1 on failure.
            if idx != -1:
                header_part = bytes(self.buffer[:idx])
                start_of_body = bytes(self.buffer[idx + len(terminator):])
                return header_part, start_of_body

        # Terminator not found, return all we have
        return self.buffer, b""
