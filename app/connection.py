import socket

from app.config import settings
from app.logging import logger

from app.http_protocol.parser import HTTPParser
from app.http_protocol.response import HTTPResponse
from app.http_protocol.request import HTTPRequest


class ConnectionHandler:
    """
    Handle a single client connection lifecycle.
    (supports keep-alive and multiple requests per connection)
    """

    def __init__(
        self, connection: socket.socket, address, conn_timeout: float
    ):
        self.conn: socket.socket = connection
        self.address = address
        self.buffer: bytes = b""
        self._running: bool = True
        self.keepalive_timeout: float = conn_timeout
        self.conn.settimeout(conn_timeout)

    def handle_connection(self):
        """
        Main connection loop to handle Http-Requests-Response cycle.
        accepts multiple requests on the same TCP connection if
        client requests keep-alive.
        how it works (generally)? steps:
        1- extracts raw-request and builds HTTPRequest-Obj
        2- analyze HTTPRequest-Obj and build a proper HTTPResponse-Obj
        3- decide how to send Http-Response bytes ('chunked transferring' or
        send whole Response 'at once' -> if chunked transferring -> handle it)
        4- decide whether to keep connection alive or not
        """

        requests_count = 0  # num of requests is served on this connection
        max_requests = settings.MAX_REQUESTS_PER_CONNECTION
        while self._running and requests_count < max_requests:
            try:
                # step_1: raw-request -> HTTPRequest-Obj
                try:
                    request = self._extract_raw_request()
                    if request is None:
                        response_obj = HTTPResponse(
                            status_code=400,
                            body=b"Bad Request",
                            mem_type="text/plain"
                        )
                        response = response_obj.build_response()
                        self.conn.sendall(response)
                        break
                        # first: make self._running=False
                        # then: back to `server.py:line70`: connection.close()
                        # (malformed requests -> close)
                except socket.timeout:
                    raise

                # step_2: analyze HTTPRequest-Obj -> proper HTTPResponse-Obj
                try:
                    response_obj = self._handle_request(request)
                except Exception as e:
                    logger.exception("Error while handling request: %s", e)
                    response_obj = HTTPResponse(
                        status_code=500,
                        body=b"Internal Server Error",
                        mem_type="text/plain"
                    )
                    response = response_obj.build_response()
                    self.conn.sendall(response)
                    break  # same as previous 'break' -> connection.close()

                # step_3: decide how to send Http-Response bytes
                if response_obj.chunked and callable(response_obj.iter_body):
                    # If chunked response provided:
                    # first: send headers with `Transfer-Encoding: chunked`
                    http_header = response_obj.build_response()
                    self.conn.sendall(http_header)
                    # then: stream chunks
                    for chunk in response_obj.iter_body():
                        if not chunk:
                            continue
                        size_hex = f"{len(chunk):X}\r\n".encode("ascii")
                        self.conn.sendall(size_hex + chunk + b"\r\n")
                    # after streaming finished, send terminating chunk
                    self.conn.sendall(b"0\r\n\r\n")
                else:
                    response = response_obj.build_response()
                    self.conn.sendall(response)

                # step_4 : decide whether to keep connection alive or not
                if self._keep_connection_alive(request):
                    # keep alive -> continue loop, but reset timeout
                    requests_count += 1
                    self.conn.settimeout(self.keepalive_timeout)
                    continue
                else:
                    break

            except socket.timeout:
                logger.debug("Connection timed out (idle)")
                break
            except ConnectionResetError:
                logger.debug("Connection reset by peer")
                break
            except Exception as e:
                logger.exception("Unexpected connection error: %s", e)
                break
        else:
            if requests_count == max_requests:
                logger.info(
                    "Connection from '%s:%s' reached max-requests-limitation",
                    *self.address
                )

        self._running = False

    def _extract_raw_request(self) -> HTTPRequest | None:
        """ extract raw Http-Request from buffer and make HTTPRequest-Obj """

        try:
            header_part, remaining = self._read_until_body_header_terminator()
            if not header_part:
                logger.info("[-] Empty request from '%s:%d'", *self.address)
                return None
        except socket.timeout:
            raise

        try:
            request = HTTPParser.parse_http_request(
                header_part, remaining, self.conn
            )
            logger.info(
                "%s %s %s (from: %s:%d)",
                request.method,
                request.path,
                request.version,
                *self.address
            )
            return request
        except Exception as err:
            logger.info(f"[!] Failed to parse request: {err}")
            return None

    @staticmethod
    def _handle_request(request: HTTPRequest) -> HTTPResponse:
        """
        gets a HTTPRequest-Obj, analyze it, and build a proper HTTPResponse-Obj
        """
        if request.method.upper() == "HEAD":  # just send `Headers`
            response_obj = HTTPResponse(body=b"", is_for_head_method=True)
            return response_obj
        # elif ...:
        #   handle 'routing'
        #   handle "Expect: 100-continue"
        #   handle "provide chunk body transferring properly"
        #   etc...
        else:
            body = (
                f"<br>"
                f"<h1 style='text-align: center;'>"
                f"  I'm developing my own HTTPServer... :)))\n"
                f"You requested {request.path!r}\n"
                f"</h1>"
            ).encode("utf-8")
            response = HTTPResponse(body=body, mem_type="text/html")
            return response

    def _read_until_body_header_terminator(self) -> tuple[bytes, bytes]:
        """
        Read from socket until the terminator ('\r\n\r\n') is found.
        This uses a buffer and may read more bytes than strictly necessary;
        the extra bytes are returned as 'remaining' so caller can process them.
        Returns a tuple (header_part, remaining).
        header_part: data before terminator / remaining: remaining bytes
        after terminator on buffer (starting bytes of body)
        """

        terminator = b"\r\n\r\n"
        while True:
            try:
                chunk = self.conn.recv(2048)  # 2 KB
            except socket.timeout:
                raise
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

        # Terminator not found, return all we have as header_part
        return self.buffer, b""

    @staticmethod
    def _keep_connection_alive(request: HTTPRequest) -> bool:
        """ Decide whether to keep connection alive or close it,
        based on Request headers and its HTTP-version """

        connection_header = request.headers.get("connection", "")
        if request.version.upper().startswith("HTTP/1.1"):
            # For HTTP/1.1 default is `keep-alive` unless "Connection: close"
            if connection_header.lower() == "close":
                return False
            else:
                return True
        else:
            # For HTTP/1.0 default is `close` unless "Connection: keep-alive"
            if connection_header.lower() == "keep-alive":
                return True
            else:
                return False
