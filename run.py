import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

from app import create_app
app = create_app()

if __name__ == "__main__":
    from waitress import serve
    logging.info("Starting waitress server...")
    serve(app, host="0.0.0.0", port=5001, threads=4)