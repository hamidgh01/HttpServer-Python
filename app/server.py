"""
ToDo: complete the documentation for HTTPServer class later.
"""

from typing import Optional
import socket
import signal
from threading import Semaphore
from concurrent.futures import ThreadPoolExecutor, Future

from app.config import settings
from app.logging import logger
from app.connection import ConnectionHandler


class HTTPServer:
    """
    a simple, non-blocking, and multithreaded TCP server using raw sockets.
    it actually handles only Network-layer logic. handling Application-layer
    logic (parsing Http-Requests and building Http-Responses) is done by
    'ConnectionHandler' and 'HTTPParser' classes!
    """

    def __init__(self):
        # Socket/Connection attributes:
        self.host: str = settings.SOCKET_HOST
        self.port: int = settings.SOCKET_PORT
        self.backlog: int = settings.SOCKET_BACKLOG_CONNECTIONS
        self.conn_timeout: float = settings.TCP_CONNECTION_TIMEOUT
        self._sock: Optional[socket.socket] = None

        # ThreadPool attributes:
        self._executor: Optional[ThreadPoolExecutor] = None
        self._max_workers: int = settings.THREADPOOL_MAX_WORKERS
        # self._futures: list[Future] = []
        self._semaphore = Semaphore(settings.THREADPOOL_MAX_TASKS_SEMAPHORE)

        # general attributes:
        self._dev_mode: bool = settings.DEVELOPMENT_MODE
        self._running: bool = False

    def start(self):
        logger.info(f"Server is running on http://{self.host}:{self.port}\n")

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self._dev_mode:  # Allow quick reuse for development
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(self.backlog)
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._running = True

        # Allow CTRL+C to break immediately
        def _sigint(signum, frame):
            raise KeyboardInterrupt()

        signal.signal(signal.SIGINT, _sigint)

        try:
            logger.info("Waiting for a connection...")
            while True:
                connection, address = self._sock.accept()
                logger.info("[+] Accepted connection from '%s:%d'", *address)

                # block here if semaphore is used (limits queued tasks)
                self._semaphore.acquire()
                future = self._executor.submit(
                    self._handle_connection, connection, address
                )
                # self._futures.append(future)

                def _done_callback(fut: Future):
                    """ done-callback function for future-objects
                    to release semaphore and log exceptions """
                    self._semaphore.release()
                    exc = fut.exception()
                    if exc:
                        logger.exception(
                            "Exception in connection handler: %s", exc
                        )
                    # self._futures.remove(fut)
                    del fut

                future.add_done_callback(_done_callback)

        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self._shutdown()

    def _handle_connection(self, connection, address):
        """
        this method is used to handle each new-established connections in a
        new worker-thread. (connection-handling is done by `ConnectionHandler`)
        """
        try:
            handler = ConnectionHandler(
                connection, address, conn_timeout=self.conn_timeout
            )
            logger.info("Handling connection from '%s:%d'", *address)
            handler.handle_connection()
        except Exception as e:
            logger.exception(
                "Error handling client %s:%d: %s", *address, e
            )
        finally:
            try:
                connection.close()
            except Exception:
                pass
            logger.info("[x] Closed connection: '%s:%d'", *address)

    def _shutdown(self):
        if self._running:
            logger.info("Server shut down!")
        self._running = False

        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

        if self._executor:
            # wait for currently running tasks to finish
            self._executor.shutdown(wait=True)
            self._executor = None
