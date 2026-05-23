from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api import router
from backend.app.core.logging import configure_logging
from backend.app.db.session import Base, SessionLocal, engine, ensure_sqlite_schema
from backend.app.services.cases import backfill_case_latest_recommendations


configure_logging()
Base.metadata.create_all(bind=engine)
ensure_sqlite_schema()
with SessionLocal() as startup_db:
    backfill_case_latest_recommendations(startup_db)

app = FastAPI(title="FirstWord API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": f"Unexpected local error: {exc}"})


app.include_router(router)
