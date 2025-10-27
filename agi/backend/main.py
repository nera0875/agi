from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import tasks

app = FastAPI(
    title="Task Manager AGI API",
    description="Backend API for the Task Manager AGI application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/api", tags=["tasks"])

@app.get("/")
async def root():
    return {"message": "Task Manager AGI API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is operational"}