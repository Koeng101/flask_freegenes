"""init

Revision ID: 00e43c68180b
Revises: 
Create Date: 2019-03-25 14:28:57.568437

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '00e43c68180b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('collections',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('time_updated', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('parent_id', postgresql.UUID(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('readme', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['collections.uuid'], ),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.create_table('parts',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('time_updated', sa.DateTime(timezone=True), nullable=True),
    sa.Column('gene_id', sa.String(), nullable=True),
    sa.Column('part_type', sa.String(), nullable=True),
    sa.Column('original_sequence', sa.String(), nullable=True),
    sa.Column('optimized_sequence', sa.String(), nullable=True),
    sa.Column('synthesized_sequence', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('genbank', sa.JSON(), nullable=True),
    sa.Column('vector', sa.String(), nullable=True),
    sa.Column('primer_for', sa.String(), nullable=True),
    sa.Column('primer_rev', sa.String(), nullable=True),
    sa.Column('barcode', sa.String(), nullable=True),
    sa.Column('vbd', sa.String(), nullable=True),
    sa.Column('resistance', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.create_table('tags',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tag', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.create_table('users',
    sa.Column('id', postgresql.UUID(), nullable=False),
    sa.Column('username', sa.String(length=32), nullable=True),
    sa.Column('password_hash', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_table('virtual',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('gene_id', sa.String(), nullable=False),
    sa.Column('gene_name', sa.String(), nullable=True),
    sa.Column('virtual_type', sa.String(), nullable=False),
    sa.Column('vbd', sa.String(), nullable=True),
    sa.Column('resistance', sa.String(), nullable=True),
    sa.Column('sequence', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('gene_id'),
    sa.UniqueConstraint('uuid')
    )
    op.create_table('tags_to',
    sa.Column('tags_uuid', postgresql.UUID(), nullable=False),
    sa.Column('collection_uuid', postgresql.UUID(), nullable=False),
    sa.Column('part_uuid', postgresql.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['collection_uuid'], ['collections.uuid'], ),
    sa.ForeignKeyConstraint(['part_uuid'], ['parts.uuid'], ),
    sa.ForeignKeyConstraint(['tags_uuid'], ['tags.uuid'], ),
    sa.PrimaryKeyConstraint('tags_uuid', 'collection_uuid', 'part_uuid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tags_to')
    op.drop_table('virtual')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
    op.drop_table('tags')
    op.drop_table('parts')
    op.drop_table('collections')
    # ### end Alembic commands ###
