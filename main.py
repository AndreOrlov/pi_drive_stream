import uvicorn
import signal
import sys

from app.config import config
from app.hw.motors_stub import cleanup_servo


def signal_handler(sig, frame):
    print("\n[SHUTDOWN] Cleaning up servo resources...")
    cleanup_servo()
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
