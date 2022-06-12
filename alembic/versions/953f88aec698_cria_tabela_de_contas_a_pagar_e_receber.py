"""Cria tabela de contas a pagar e receber

Revision ID: 953f88aec698
Revises: 
Create Date: 2022-06-12 10:20:50.219387

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '953f88aec698'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'contas_a_pagar_e_receber',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('descricao', sa.String(length=30), nullable=True),
        sa.Column('valor', sa.Numeric(), nullable=True),
        sa.Column('tipo', sa.String(length=30), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('contas_a_pagar_e_receber')
