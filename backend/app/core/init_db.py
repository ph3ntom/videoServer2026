"""
Database initialization script
Creates admin user if it doesn't exist
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.core.config import settings


async def init_db():
    """Initialize database with admin user"""
    async with AsyncSessionLocal() as session:
        # Check if admin user exists
        result = await session.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        admin_user = result.scalar_one_or_none()

        if admin_user:
            print(f"Admin user already exists: {settings.ADMIN_EMAIL}")
            return

        # Create admin user
        admin_user = User(
            email=settings.ADMIN_EMAIL,
            username="admin",
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )

        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)

        print(f"✅ Admin user created: {settings.ADMIN_EMAIL}")
        print(f"   Password: {settings.ADMIN_PASSWORD}")
        print(f"   Role: {admin_user.role.value}")


if __name__ == "__main__":
    asyncio.run(init_db())
