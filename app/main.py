import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.supervisors import ChangeReload

from app.Shared.router.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Print log messages to the console
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(docs_url="/", redoc_url=None, title="FastAPI App")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(
    api_router,
    prefix="/api/v1",
    tags=["API v1"]
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI application!"}

if __name__ == '__main__':
    config = uvicorn.Config("app.main:app", port=20000, host="0.0.0.0", log_level="info", reload=True)
    server = uvicorn.Server(config)

    reload = True

    if reload:
        sock = config.bind_socket()
        ChangeReload(config, target=server.run, sockets=[sock]).run()
    else:
        server.run()
