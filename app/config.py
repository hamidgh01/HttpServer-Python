from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """
    TCP_CONNECTION_TIMEOUT:
        amount of time (in secondes) the server sets as keep-alive timeout
        for each TCP connection

    MAX_REQUESTS_PER_CONNECTION:
        max number of requests the server will serve on a single connection

    THREADPOOL_MAX_WORKERS:
        max number of worker-threads (connection handler threads) in ThreadPool

    THREADPOOL_MAX_TASKS_SEMAPHORE:
        max number of (`submitted` or `queued`) tasks in ThreadPoolExecutor
        (prevent unlimited queued sockets in executor’s internal task-queue)
    """

    PROJECT_NAME = "HTTPServer-by-hamidgh01"
    DEVELOPMENT_MODE = True

    # Socket settings
    SOCKET_HOST: str = "127.0.0.1"
    SOCKET_PORT: int = 8080
    SOCKET_BACKLOG_CONNECTIONS: int = 250

    # Connection settings
    TCP_CONNECTION_TIMEOUT: float = 10.0
    MAX_REQUESTS_PER_CONNECTION: int = 8

    # ThreadPool settings
    THREADPOOL_MAX_WORKERS: int = 32
    THREADPOOL_MAX_TASKS_SEMAPHORE: int = 96  # (32 in work / 64 in queue)


settings = Settings()
