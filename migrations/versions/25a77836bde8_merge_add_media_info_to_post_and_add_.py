"""merge add media info to post and add profile pic and name to user

Revision ID: 25a77836bde8
Revises: 3338863d2def, 700ec1da57fe
Create Date: 2021-07-21 17:19:41.041612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25a77836bde8'
down_revision = ('3338863d2def', '700ec1da57fe')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
