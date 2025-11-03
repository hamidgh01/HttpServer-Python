from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """ ToDo: add a one-line explanation for each one """

    PROJECT_NAME: str = "HTTPServer-by-hamidgh01"
    TCP_CONNECTION_TIMEOUT: float = 5.0  # seconds
    MAX_PIPELINED: int = 8


settings = Settings()
