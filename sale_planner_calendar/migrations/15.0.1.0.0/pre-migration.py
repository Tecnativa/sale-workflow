# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def set_is_base_recurrent_event(env):
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE calendar_event ADD COLUMN IF NOT EXISTS is_base_recurrent_event BOOL;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE calendar_event ce
        SET is_base_recurrent_event = CASE
            WHEN ce.id = cr.base_event_id THEN true
            ELSE false
            END
        FROM calendar_recurrence cr
        WHERE ce.recurrence_id = cr.id
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    set_is_base_recurrent_event(env)
