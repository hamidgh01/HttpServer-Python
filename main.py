from app.server import HTTPServer
from app.config import settings


def show_server_settings(settings_obj):
    raise NotImplementedError


if __name__ == "__main__":
    # show_server_settings(settings)
    server = HTTPServer()
    server.start()
