"""add webhook_event table

Revision ID: 15eae08f6090
Revises: e65b250a8751
Create Date: 2026-04-28 11:23:52.463361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15eae08f6090'
down_revision: Union[str, Sequence[str], None] = 'e65b250a8751'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False, index=True),
        sa.Column('provider_payment_id', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('received', 'processed', 'failed', name='webhookeventstatus'), nullable=False, server_default='received'),
        sa.Column('payload', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_webhook_events_created_at', 'webhook_events', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_webhook_events_created_at', 'webhook_events')
    op.drop_table('webhook_events')
    op.execute("DROP TYPE IF EXISTS webhookeventstatus")
