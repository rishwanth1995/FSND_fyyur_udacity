"""empty message

Revision ID: 021632339b94
Revises: 00f969f620cf
Create Date: 2020-05-09 20:13:09.282568

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '021632339b94'
down_revision = '00f969f620cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('website_link', sa.String(length=500), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'website_link')
    # ### end Alembic commands ###