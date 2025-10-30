from app.server import HTTPServer

if __name__ == "__main__":
    server = HTTPServer(development_mode=True)
    server.start()
