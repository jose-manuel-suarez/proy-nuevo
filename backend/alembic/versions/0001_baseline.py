"""Baseline revision.

The bootstrap release defines no domain tables yet. This revision exists so
that the migration chain has a head, CI can prove that an empty database
upgrades cleanly, and the first domain migration has a parent.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-26
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
