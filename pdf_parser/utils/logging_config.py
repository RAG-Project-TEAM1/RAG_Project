import logging

def setup_logging():
    logging.basicConfig(
        filename="parse_failures.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )