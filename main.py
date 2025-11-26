import logging
import signal
import sys

import uvicorn

from app.config import config
from app.hw.servos import cleanup_servo


def signal_handler(sig, frame):
    print("\n[SHUTDOWN] Cleaning up servo resources...")
    cleanup_servo()
    sys.exit(0)


def main() -> None:
    # Configure logging for the entire application
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:     %(name)s - %(message)s",
    )

    # Set log level for our app modules
    logging.getLogger("app").setLevel(logging.INFO)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    uvicorn.run(
        "app.web.server:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
