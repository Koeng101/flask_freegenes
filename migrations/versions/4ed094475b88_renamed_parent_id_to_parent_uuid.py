"""renamed parent_id to parent_uuid

Revision ID: 4ed094475b88
Revises: 62fcac0eea50
Create Date: 2019-03-25 18:47:25.153503

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4ed094475b88'
down_revision = '62fcac0eea50'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('collections', sa.Column('parent_uuid', postgresql.UUID(), nullable=True))
    op.drop_constraint('collections_parent_id_fkey', 'collections', type_='foreignkey')
    op.create_foreign_key(None, 'collections', 'collections', ['parent_uuid'], ['uuid'])
    op.drop_column('collections', 'parent_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('collections', sa.Column('parent_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'collections', type_='foreignkey')
    op.create_foreign_key('collections_parent_id_fkey', 'collections', 'collections', ['parent_id'], ['uuid'])
    op.drop_column('collections', 'parent_uuid')
    # ### end Alembic commands ###
