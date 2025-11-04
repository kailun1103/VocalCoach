from fastapi import FastAPI

from .routes import chat, dictionary, forms, grammar, speech


def register_routes(app: FastAPI) -> None:
    """Attach API routers to the FastAPI application."""
    app.include_router(speech.router)
    app.include_router(chat.router)
    app.include_router(dictionary.router)
    app.include_router(grammar.router)
    app.include_router(forms.router)


__all__ = ["register_routes"]
