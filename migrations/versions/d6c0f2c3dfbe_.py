"""empty message

Revision ID: d6c0f2c3dfbe
Revises: 
Create Date: 2022-04-11 21:19:57.276686

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd6c0f2c3dfbe'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('groups',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('modified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('kgcId', sa.Integer(), nullable=False),
    sa.Column('groupName', sa.String(length=255), nullable=False),
    sa.Column('country', sa.String(length=255), nullable=False),
    sa.Column('startYear', sa.Integer(), nullable=True),
    sa.Column('endYear', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('kgcId')
    )
    op.create_index(op.f('ix_groups_groupName'), 'groups', ['groupName'], unique=False)
    op.create_index(op.f('ix_groups_created_at'), 'groups', ['created_at'], unique=False)
    op.create_index(op.f('ix_groups_modified_at'), 'groups', ['modified_at'], unique=False)
    op.create_table('user',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('modified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('token', sa.String(length=32), nullable=True),
    sa.Column('token_expiration', sa.DateTime(), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_user_created_at'), 'user', ['created_at'], unique=False)
    op.create_index(op.f('ix_user_modified_at'), 'user', ['modified_at'], unique=False)
    op.create_index(op.f('ix_user_name'), 'user', ['name'], unique=False)
    op.create_index(op.f('ix_user_token'), 'user', ['token'], unique=True)
    op.create_table('organizations',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('modified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('facId', sa.Integer(), nullable=False),
    sa.Column('kgcId', sa.Integer(), nullable=True),
    sa.Column('facName', sa.String(length=767), nullable=False),
    sa.Column('startYear', sa.Integer(), nullable=True),
    sa.Column('endYear', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['kgcId'], ['groups.kgcId'], ),
    sa.PrimaryKeyConstraint('facId'),
    sa.UniqueConstraint('facId')
    )
    op.create_index(op.f('ix_organizations_created_at'), 'organizations', ['created_at'], unique=False)
    op.create_index(op.f('ix_organizations_modified_at'), 'organizations', ['modified_at'], unique=False)
    op.create_table('nonviolence',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('modified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('facId', sa.Integer(), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('economicNoncooperation', sa.Integer(), nullable=False),
    sa.Column('protestDemonstration', sa.Integer(), nullable=False),
    sa.Column('nonviolentIntervention', sa.Integer(), nullable=False),
    sa.Column('socialNoncooperation', sa.Integer(), nullable=False),
    sa.Column('institutionalAction', sa.Integer(), nullable=False),
    sa.Column('politicalNoncooperation', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['facId'], ['organizations.facId'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nonviolence_facId'), 'nonviolence', ['facId'], unique=False)
    op.create_index(op.f('ix_nonviolence_created_at'), 'nonviolence', ['created_at'], unique=False)
    op.create_index(op.f('ix_nonviolence_modified_at'), 'nonviolence', ['modified_at'], unique=False)
    op.create_table('violence',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('modified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('facId', sa.Integer(), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('againstState', sa.Integer(), nullable=False),
    sa.Column('againstStateFatal', sa.Integer(), nullable=False),
    sa.Column('againstOrg', sa.Integer(), nullable=False),
    sa.Column('againstOrgFatal', sa.Integer(), nullable=False),
    sa.Column('againstIngroup', sa.Integer(), nullable=False),
    sa.Column('againstIngroupFatal', sa.Integer(), nullable=False),
    sa.Column('againstOutgroup', sa.Integer(), nullable=False),
    sa.Column('againstOutgroupFatal', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['facId'], ['organizations.facId'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_violence_facId'), 'violence', ['facId'], unique=False)
    op.create_index(op.f('ix_violence_created_at'), 'violence', ['created_at'], unique=False)
    op.create_index(op.f('ix_violence_modified_at'), 'violence', ['modified_at'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_violence_modified_at'), table_name='violence')
    op.drop_index(op.f('ix_violence_created_at'), table_name='violence')
    op.drop_index(op.f('ix_violence_facId'), table_name='violence')
    op.drop_table('violence')
    op.drop_index(op.f('ix_nonviolence_modified_at'), table_name='nonviolence')
    op.drop_index(op.f('ix_nonviolence_created_at'), table_name='nonviolence')
    op.drop_index(op.f('ix_nonviolence_facId'), table_name='nonviolence')
    op.drop_table('nonviolence')
    op.drop_index(op.f('ix_organizations_modified_at'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_created_at'), table_name='organizations')
    op.drop_table('organizations')
    op.drop_index(op.f('ix_user_token'), table_name='user')
    op.drop_index(op.f('ix_user_name'), table_name='user')
    op.drop_index(op.f('ix_user_modified_at'), table_name='user')
    op.drop_index(op.f('ix_user_created_at'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_groups_modified_at'), table_name='groups')
    op.drop_index(op.f('ix_groups_created_at'), table_name='groups')
    op.drop_index(op.f('ix_groups_groupName'), table_name='groups')
    op.drop_table('groups')
    # ### end Alembic commands ###
