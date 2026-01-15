"""add_performance_indexes

Revision ID: a1b2c3d4e5f6
Revises: 2f1e7b15dd7f
Create Date: 2026-01-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2f1e7b15dd7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on videos.view_count for sorting by popularity
    op.create_index('ix_videos_view_count', 'videos', ['view_count'], unique=False)

    # Add composite index on videos (status, view_count) for filtered sorting
    op.create_index('ix_videos_status_view_count', 'videos', ['status', 'view_count'], unique=False)

    # Add composite index on videos (status, created_at) for filtered sorting by date
    # Note: created_at already has an index, but composite with status is more efficient
    op.create_index('ix_videos_status_created_at', 'videos', ['status', 'created_at'], unique=False)

    # Add index on ratings.video_id for average rating calculations
    # This helps with JOIN performance when calculating video ratings
    op.create_index('ix_ratings_video_id', 'ratings', ['video_id'], unique=False)


def downgrade() -> None:
    # Remove indexes in reverse order
    op.drop_index('ix_ratings_video_id', table_name='ratings')
    op.drop_index('ix_videos_status_created_at', table_name='videos')
    op.drop_index('ix_videos_status_view_count', table_name='videos')
    op.drop_index('ix_videos_view_count', table_name='videos')
