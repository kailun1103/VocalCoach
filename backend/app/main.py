from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import register_routes
from .core import configure_logging

configure_logging()

app = FastAPI(
    title="EnglishTalk API",
    version="0.1.0",
    description="Voice processing endpoints plus chat proxy for local LLMs.",
)

register_routes(app)


def _attach_frontend(app: FastAPI) -> None:
    """Optionally serve the built frontend if available."""
    try:
        root_dir = Path(__file__).resolve().parents[2]
        dist_dir = root_dir / "frontend" / "dist"
        if not dist_dir.exists():
            return

        app.mount("/app", StaticFiles(directory=str(dist_dir), html=True), name="app")

        @app.get("/app", include_in_schema=False)  # type: ignore
        async def app_index() -> FileResponse:
            return FileResponse(str(dist_dir / "index.html"))
    except Exception:  # pragma: no cover - defensive: do not crash API if mount fails
        return


_attach_frontend(app)
