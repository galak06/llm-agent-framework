"""resize memory_embeddings to voyage embedding dim

Revision ID: a1b2c3d4e5f6
Revises: ffc0947f4d17
Create Date: 2026-04-27 12:00:00.000000

The initial migration created memory_embeddings.embedding as Vector(256),
matching the SHA-based fallback embedder. This migration resizes it to 1024
to match Voyage AI (voyage-3-large / voyage-3.5). The table has no
production data yet, so we drop+recreate the column instead of trying
to cast vectors of incompatible dimensions.
"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy.vector
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ffc0947f4d17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('memory_embeddings', 'embedding')
    op.add_column(
        'memory_embeddings',
        sa.Column(
            'embedding',
            pgvector.sqlalchemy.vector.VECTOR(dim=1024),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('memory_embeddings', 'embedding')
    op.add_column(
        'memory_embeddings',
        sa.Column(
            'embedding',
            pgvector.sqlalchemy.vector.VECTOR(dim=256),
            nullable=False,
        ),
    )
