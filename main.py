import uvicorn

from app.config import config


def main() -> None:
    uvicorn.run(
        "app.web.server:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
    )


if __name__ == "__main__":
    main()
