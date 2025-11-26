import logging

# Configure logging BEFORE other imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

import uvicorn
import signal
import sys

from app.config import config
from app.hw.servos import cleanup_servo
from app.video import cleanup_camera


def signal_handler(sig, frame):
    print("\n[SHUTDOWN] Cleaning up resources...")
    cleanup_servo()
    cleanup_camera()
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    uvicorn.run(
        "app.web.server:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
    )


if __name__ == "__main__":
    main()
