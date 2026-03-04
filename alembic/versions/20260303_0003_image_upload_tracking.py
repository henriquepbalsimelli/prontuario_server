"""image upload tracking fields

Revision ID: 20260303_0003
Revises: 20260227_0002
Create Date: 2026-03-03 08:00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260303_0003"
down_revision: str | None = "20260227_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "image",
        sa.Column("upload_status", sa.String(length=30), nullable=False, server_default="pending"),
    )
    op.add_column("image", sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("image", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.add_column("image", sa.Column("etag", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("image", "etag")
    op.drop_column("image", "file_size_bytes")
    op.drop_column("image", "uploaded_at")
    op.drop_column("image", "upload_status")
