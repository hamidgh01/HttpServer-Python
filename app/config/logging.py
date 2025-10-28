import logging
# from settings import ...


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("HTTPServer")  # put setting.PROJECT_NAME here
