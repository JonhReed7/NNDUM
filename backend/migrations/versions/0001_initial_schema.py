"""Create the initial application schema."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

analysis_status = postgresql.ENUM(
    "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", name="AnalysisStatus", create_type=False
)


def upgrade() -> None:
    analysis_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("github_access_token", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "analyses",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("repo_url", sa.String(), nullable=False),
        sa.Column("status", postgresql.ENUM("PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", name="AnalysisStatus", create_type=False), server_default="PENDING", nullable=False),
        sa.Column("metrics_result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_table(
        "teams",
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
    )
    op.create_table(
        "projects",
        sa.Column("team_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("repo_url", sa.String(), nullable=False),
        sa.Column("branch", sa.String(), server_default="main", nullable=False),
        sa.Column("timezone", sa.String(), server_default="UTC+0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
    )
    op.create_table(
        "team_members",
        sa.Column("team_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("git_email", sa.String(), nullable=False),
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_table(
        "sprints",
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("statistics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
    )


def downgrade() -> None:
    op.drop_table("sprints")
    op.drop_table("team_members")
    op.drop_table("projects")
    op.drop_table("teams")
    op.drop_table("analyses")
    op.drop_table("users")
    analysis_status.drop(op.get_bind(), checkfirst=True)
