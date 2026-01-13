from fastapi import APIRouter
from app.api.v1 import auth, videos, tags, ratings, watch_history

api_router = APIRouter()

# Include auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Include video routes
api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])

# Include tag routes
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])

# Include rating routes
api_router.include_router(ratings.router, prefix="/videos", tags=["Ratings"])

# Include watch history routes
api_router.include_router(watch_history.router, prefix="/videos", tags=["Watch History"])
