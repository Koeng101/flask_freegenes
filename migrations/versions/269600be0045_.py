"""empty message

Revision ID: 269600be0045
Revises: 91cdbc91c1ca
Create Date: 2019-03-25 15:10:46.265206

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '269600be0045'
down_revision = '91cdbc91c1ca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('tags_to_part_uuid_fkey', 'tags_to', type_='foreignkey')
    op.drop_column('tags_to', 'part_uuid')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tags_to', sa.Column('part_uuid', postgresql.UUID(), autoincrement=False, nullable=False))
    op.create_foreign_key('tags_to_part_uuid_fkey', 'tags_to', 'parts', ['part_uuid'], ['uuid'])
    # ### end Alembic commands ###
