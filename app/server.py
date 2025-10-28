"""
ToDo: complete the documentation for HTTPServer class later.
"""

from typing import Optional
import socket

from app.config.logging import logger


class HTTPServer:
    """
    a simple, blocking, single-threaded, and synchronous TCP server using
    raw sockets. it actually handles only the Network-layer logic. handling
    the Application-layer logic (parsing Http-Requests and building
    Http-Response) is done by 'ConnectionHandler' and 'HTTPParser' classes!
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        backlog: int = 5,
        development_mode: bool = True
    ):
        self.host = host
        self.port = port
        self.backlog = backlog
        self._dev_mode = development_mode
        self._sock: Optional[socket.socket] = None
        self._running: bool = False

    def start(self):
        logger.info(f"Server is running on http://{self.host}:{self.port}\n")

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self._dev_mode:  # Allow quick reuse for development
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(self.backlog)
        self._running = True

        try:
            while True:
                logger.info("Waiting for a connection...")
                conn, addr = self._sock.accept()
                # extract connection-info ...
                logger.info("[+] Accepted connection from '%s:%d'", *addr)
                try:
                    # handle the connection and received HTTPRequest here
                    pass
                except Exception as e:
                    logger.exception(
                        "Error handling client %s:%d: %s", *addr, e
                    )
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    logger.info("[x] Closed connection: '%s:%d'\n", *addr)
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.shutdown()

    def shutdown(self):
        if self._running:
            logger.info("Server shut down!")
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
