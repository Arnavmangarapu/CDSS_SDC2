from fastapi import FastAPI
from backend.api.routes import router

app = FastAPI(
    title="Multi-Agent Graph-RAG CDSS",
    description="Research prototype backend for clinical decision support",
    version="0.1.0"
)

from fastapi.staticfiles import StaticFiles

app.include_router(router)

# Mount the frontend UI
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
