"""Update BusinessCard model

Revision ID: bd0316b8ea3b
Revises: 
Create Date: 2024-07-06 20:10:44.436729

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd0316b8ea3b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('business_card', schema=None) as batch_op:
        batch_op.alter_column('social_media',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=True)
        batch_op.alter_column('products_services',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('business_card', schema=None) as batch_op:
        batch_op.alter_column('products_services',
               existing_type=sa.JSON(),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('social_media',
               existing_type=sa.JSON(),
               type_=sa.TEXT(),
               existing_nullable=True)

    # ### end Alembic commands ###