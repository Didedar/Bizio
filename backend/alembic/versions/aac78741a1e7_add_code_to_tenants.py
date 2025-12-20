"""add_code_to_tenants

Revision ID: aac78741a1e7
Revises: 
Create Date: 2025-11-19 17:34:07.823684

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aac78741a1e7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add code column to tenants table
    op.add_column('tenants', sa.Column('code', sa.String(length=64), nullable=True))
    # Create unique index on code column
    op.create_index(op.f('ix_tenants_code'), 'tenants', ['code'], unique=True)


def downgrade() -> None:
    # Drop index first
    op.drop_index(op.f('ix_tenants_code'), table_name='tenants')
    # Drop code column
    op.drop_column('tenants', 'code')

