from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from core.api.routers import system, backup, projects

app = FastAPI(
    title="NHI Brain API",
    description="Neural Home Infrastructure Control Plane",
    version="1.1.0"
)

# CORS Configuration (Enable access from Dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev status. In prod, lock to dashboard IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(system.router, prefix="/system", tags=["System"])
app.include_router(backup.router, prefix="/backup", tags=["Backup"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])

@app.get("/")
async def root():
    return {"status": "online", "system": "nhi-core", "version": "1.1.0"}
