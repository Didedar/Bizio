"""add_deal_additional_fields

Revision ID: 44a8f9be5e8d
Revises: aac78741a1e7
Create Date: 2025-11-29 21:18:53.260122

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44a8f9be5e8d'
down_revision = 'aac78741a1e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if columns already exist (for cases where DB was manually updated)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('deals')]
    
    # Add new columns to deals table only if they don't exist
    if 'start_date' not in existing_columns:
        op.add_column('deals', sa.Column('start_date', sa.DateTime(), nullable=True))
    if 'completion_date' not in existing_columns:
        op.add_column('deals', sa.Column('completion_date', sa.DateTime(), nullable=True))
    if 'source' not in existing_columns:
        op.add_column('deals', sa.Column('source', sa.String(length=128), nullable=True))
    if 'source_details' not in existing_columns:
        op.add_column('deals', sa.Column('source_details', sa.String(length=1024), nullable=True))
    if 'deal_type' not in existing_columns:
        op.add_column('deals', sa.Column('deal_type', sa.String(length=64), nullable=True))
    if 'is_available_to_all' not in existing_columns:
        op.add_column('deals', sa.Column('is_available_to_all', sa.Boolean(), nullable=False, server_default='1'))
    if 'responsible_id' not in existing_columns:
        op.add_column('deals', sa.Column('responsible_id', sa.Integer(), nullable=True))
    if 'comments' not in existing_columns:
        op.add_column('deals', sa.Column('comments', sa.Text(), nullable=True))
    if 'recurring_settings' not in existing_columns:
        op.add_column('deals', sa.Column('recurring_settings', sa.JSON(), nullable=True))
    
    # Create indexes only if they don't exist
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('deals')]
    if 'ix_deals_source' not in existing_indexes:
        op.create_index(op.f('ix_deals_source'), 'deals', ['source'])
    if 'ix_deals_responsible_id' not in existing_indexes:
        op.create_index(op.f('ix_deals_responsible_id'), 'deals', ['responsible_id'])
    
    # Create association table for deal observers only if it doesn't exist
    existing_tables = inspector.get_table_names()
    if 'deal_observer_association' not in existing_tables:
        op.create_table(
            'deal_observer_association',
            sa.Column('deal_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('deal_id', 'user_id')
        )
    
    # Note: Foreign key constraint for responsible_id is handled by SQLAlchemy model definition
    # SQLite doesn't support adding foreign keys via ALTER TABLE, but the constraint
    # will be enforced by the ORM layer


def downgrade() -> None:
    # Drop association table
    op.drop_table('deal_observer_association')
    
    # Drop indexes
    op.drop_index(op.f('ix_deals_responsible_id'), table_name='deals')
    op.drop_index(op.f('ix_deals_source'), table_name='deals')
    
    # Drop columns
    op.drop_column('deals', 'recurring_settings')
    op.drop_column('deals', 'comments')
    op.drop_column('deals', 'responsible_id')
    op.drop_column('deals', 'is_available_to_all')
    op.drop_column('deals', 'deal_type')
    op.drop_column('deals', 'source_details')
    op.drop_column('deals', 'source')
    op.drop_column('deals', 'completion_date')
    op.drop_column('deals', 'start_date')

