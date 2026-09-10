"""create database tables

Revision ID: 001
Revises: 
Create Date: 2024-08-03 16:48:19.881553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Copy-past to mysql
    sql = (
        """
CREATE TABLE IF NOT EXISTS UserbotTrustedUsers(
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    trusted_user_id BIGINT NOT NULL,
    PRIMARY KEY (id),
    INDEX (user_id)
);
CREATE TABLE IF NOT EXISTS UserbotUserSettings(
    user_id BIGINT NOT NULL,
    prefix VARCHAR(1) NOT NULL,
    PRIMARY KEY (user_id),
    INDEX (user_id)
);
CREATE TABLE IF NOT EXISTS UserbotVictims(
    id BIGINT NOT NULL AUTO_INCREMENT,
    infecter_id BIGINT NOT NULL,
    victimer_id BIGINT NOT NULL,
    victimer_name VARCHAR(128) NOT NULL,
    victim_expire DATETIME NOT NULL,
    bio_resource BIGINT NOT NULL,
    PRIMARY KEY (id),
    INDEX (infecter_id)
);
        """
    )


def downgrade() -> None:
    pass