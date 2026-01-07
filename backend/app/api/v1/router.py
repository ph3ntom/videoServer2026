from fastapi import APIRouter
from app.api.v1 import auth, videos

api_router = APIRouter()

# Include auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Include video routes
api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])
