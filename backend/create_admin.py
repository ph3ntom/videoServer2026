#!/usr/bin/env python3
"""
Create an admin user for StreamFlix
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def create_admin_user():
    """Create a default admin user"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if admin already exists
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.email == "admin@streamflix.com")
            )
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print("❌ Admin user already exists!")
                print(f"   Email: {existing_admin.email}")
                print(f"   Username: {existing_admin.username}")
                return

            # Create admin user
            admin_user = User(
                email="admin@streamflix.com",
                username="admin",
                full_name="StreamFlix Admin",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )

            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)

            print("✅ Admin user created successfully!")
            print(f"   Email: {admin_user.email}")
            print(f"   Username: {admin_user.username}")
            print(f"   Password: admin123")
            print(f"   Role: {admin_user.role.value}")
            print("\n⚠️  Please change the password after first login!")

        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            await db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    print("Creating admin user for StreamFlix v1.0...\n")
    asyncio.run(create_admin_user())
