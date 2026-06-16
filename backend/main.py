import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from database import SessionLocal, create_db
from seed import seed_default_data
from auth import get_current_user  # re-exported for test dependency override
from config import OPENAI_MODEL  # re-exported for test access
from routers import health, users, boards
from routers import ai as ai_router
from routers.ai import _openai_client  # re-exported for monkeypatching in tests


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    with SessionLocal() as session:
        seed_default_data(session)
    print("Application startup")
    yield
    print("Application shutdown")


app = FastAPI(title="PM Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3100",
        "http://localhost:8000",
        "http://127.0.0.1:3100",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(boards.router)
app.include_router(ai_router.router)


static_dir = Path(__file__).parent / "public" / "out"
if (static_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
else:

    @app.get("/", response_class=HTMLResponse)
    async def serve_root():
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Project Management MVP</title>
        </head>
        <body>
            <main>
                <h1>Project Management MVP</h1>
                <p>API Server Active</p>
                <p>Port: 8000</p>
                <p>Framework: FastAPI</p>
                <p>Next Steps: Build the frontend and visit <a href="/api/test">/api/test</a>.</p>
            </main>
        </body>
        </html>
        """


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
