import logging

from .bus import EventBus

# Configure logging for the app package
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to see detailed logs
    format="%(levelname)s:     %(name)s - %(message)s",
)

# Ensure app loggers use DEBUG level for troubleshooting
logging.getLogger("app").setLevel(logging.DEBUG)

event_bus = EventBus()
