import uvicorn
import typer


app = typer.Typer()


@app.command()
def main():
    pass


def server(
    host: str = "0.0.0.0",
    port: int = 8080,
):
    from open_knowledge.env import UVICORN_WORKERS

    uvicorn.run(
        "open_webui.main:app",
        host=host,
        port=port,
        forwarded_allow_ips="*",
        workers=UVICORN_WORKERS,
    )


@app.command()
def dev(
    host: str = "0.0.0.0",
    port: int = 8080,
    reload: bool = True,
):
    uvicorn.run(
        "open_webui.main:app",
        host=host,
        port=port,
        reload=reload,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    app()
