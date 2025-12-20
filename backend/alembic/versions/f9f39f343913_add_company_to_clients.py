"""add_company_to_clients

Revision ID: f9f39f343913
Revises: 44a8f9be5e8d
Create Date: 2025-12-04 13:37:39.358425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9f39f343913'
down_revision = '44a8f9be5e8d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('company', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('clients', 'company')


