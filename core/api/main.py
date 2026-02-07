from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from core.api.routers import system, backup, projects, design_system, services, docs

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
app.include_router(services.router, prefix="/services", tags=["Services"])
app.include_router(backup.router, prefix="/backup", tags=["Backup"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(design_system.router, prefix="/design-system", tags=["Design System"])
app.include_router(docs.router, prefix="/docs", tags=["Documentation"])

# Dashboard Static Files
DASHBOARD_PATH = Path("/home/ai-agent/projects/nhi-dashboard")
if DASHBOARD_PATH.exists():
    app.mount("/src", StaticFiles(directory=DASHBOARD_PATH / "src"), name="dashboard-src")
    app.mount("/static", StaticFiles(directory=DASHBOARD_PATH / "static"), name="dashboard-static")

@app.get("/")
async def root():
    return {"status": "online", "system": "nhi-core", "version": "1.1.0"}

@app.get("/dashboard")
async def dashboard():
    """Serve dashboard index.html"""
    index_path = DASHBOARD_PATH / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Dashboard not installed"}


# Reload Trigger: updated docs.py logic for Core path resolution
