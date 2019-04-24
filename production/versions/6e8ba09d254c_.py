"""empty message

Revision ID: 6e8ba09d254c
Revises: 5fb62d568543
Create Date: 2019-04-05 16:18:56.062289

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6e8ba09d254c'
down_revision = '5fb62d568543'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('containers')
    op.create_unique_constraint(None, 'organisms', ['uuid'])
    op.drop_constraint('plates_container_uuid_fkey', 'plates', type_='foreignkey')
    op.drop_column('plates', 'container_uuid')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('plates', sa.Column('container_uuid', postgresql.UUID(), autoincrement=False, nullable=True))
    op.create_foreign_key('plates_container_uuid_fkey', 'plates', 'containers', ['container_uuid'], ['uuid'])
    op.drop_constraint(None, 'organisms', type_='unique')
    op.create_table('containers',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('time_created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('time_updated', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('parent_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('child_locations', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('location', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['parent_uuid'], ['containers.uuid'], name='containers_parent_uuid_fkey'),
    sa.PrimaryKeyConstraint('uuid', name='containers_pkey')
    )
    # ### end Alembic commands ###
