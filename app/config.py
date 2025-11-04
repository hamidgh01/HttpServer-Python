from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """
    _ TCP_CONNECTION_TIMEOUT: amount of time (in secondes) the server sets
        as keep-alive timeout for each TCP connection
    _ MAX_REQUESTS_PER_CONNECTION: max number of requests the server will
        serve on a single connection
    """

    PROJECT_NAME: str = "HTTPServer-by-hamidgh01"
    TCP_CONNECTION_TIMEOUT: float = 10.0
    MAX_REQUESTS_PER_CONNECTION: int = 8


settings = Settings()
