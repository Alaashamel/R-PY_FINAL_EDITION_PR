from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.database.base import Base
from app.database.session import engine
from app.middleware.logging_middleware import LoggingMiddleware
from app.routes import appointments, auth, doctors, monitoring, patients, users
from app.utils.logger import logger

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hospital Appointment System API",
    description="Hospital management backend with JWT, database, validation, caching, testing, logging and monitoring.",
    version="1.0.0",
)

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(monitoring.router)


@app.get("/")
def root():
    return {"message": "Hospital Appointment System API", "status": "running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Hospital Appointment System API")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
