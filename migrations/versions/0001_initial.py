"""Initial NODOS response schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Older application startups created this exact initial schema directly.
    # Treat it as the initial revision rather than failing during adoption.
    if "responses" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table("responses", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(250), nullable=False), sa.Column("email", sa.String(320), nullable=False), sa.Column("preference_1", sa.String(100), nullable=False), sa.Column("preference_2", sa.String(100), nullable=False), sa.Column("additional_idea", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("email"))
    op.create_index("ix_responses_email", "responses", ["email"])
    op.create_table("response_slots", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("response_id", sa.Integer(), sa.ForeignKey("responses.id", ondelete="CASCADE"), nullable=False), sa.Column("day_id", sa.String(100), nullable=False), sa.Column("slot_id", sa.String(100), nullable=False), sa.Column("busy", sa.Boolean(), nullable=False), sa.UniqueConstraint("response_id", "day_id", "slot_id", name="uq_response_slot"))
    op.create_index("ix_response_slots_response_id", "response_slots", ["response_id"])

def downgrade():
    op.drop_table("response_slots")
    op.drop_table("responses")
