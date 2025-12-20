"""add days_until_payment to expenses

Revision ID: b1f2e3d4c567
Revises: 44a8f9be5e8d
Create Date: 2025-12-04 14:28:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1f2e3d4c567'
down_revision = 'f9f39f343913'
branch_labels = None
depends_on = None


def upgrade():
    # Add days_until_payment column to expenses table
    op.add_column('expenses', sa.Column('days_until_payment', sa.Integer(), nullable=True))


def downgrade():
    # Remove days_until_payment column from expenses table
    op.drop_column('expenses', 'days_until_payment')
