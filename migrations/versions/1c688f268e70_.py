"""empty message

Revision ID: 1c688f268e70
Revises: 269600be0045
Create Date: 2019-03-25 15:12:16.230732

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1c688f268e70'
down_revision = '269600be0045'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tags_collection',
    sa.Column('tags_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('collection_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['collection_uuid'], ['collections.uuid'], ),
    sa.ForeignKeyConstraint(['tags_uuid'], ['tags.uuid'], ),
    sa.PrimaryKeyConstraint('tags_uuid', 'collection_uuid')
    )
    op.drop_table('tags_to')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tags_to',
    sa.Column('tags_uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('collection_uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['collection_uuid'], ['collections.uuid'], name='tags_to_collection_uuid_fkey'),
    sa.ForeignKeyConstraint(['tags_uuid'], ['tags.uuid'], name='tags_to_tags_uuid_fkey')
    )
    op.drop_table('tags_collection')
    # ### end Alembic commands ###
