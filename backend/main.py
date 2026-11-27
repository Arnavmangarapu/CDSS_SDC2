from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.config import PROJECT_ROOT

app = FastAPI(
    title="Multi-Agent Graph-RAG CDSS",
    description="Research prototype backend for clinical decision support",
    version="0.1.0"
)


class FreshFrontendFiles(StaticFiles):
    """Avoid mixing a cached UI script with newly deployed report markup."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response


app.include_router(router)

# Mount the frontend UI
app.mount("/ui", FreshFrontendFiles(directory=PROJECT_ROOT / "frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
