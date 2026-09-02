"""
Anonymous usage tracking.

Records one row per tracked dashboard interaction so the number of distinct
sessions and pricing requests can be measured rather than estimated. Two events
are tracked:

    session_start  - written once when a browser session opens the dashboard
    price_request  - written each time a prop is submitted for analysis

What this measures, precisely: the Streamlit dashboard mints a random UUID per
browser session and sends it with each request. Session state resets when the tab
closes or when the hosted app sleeps, so one person visiting on five game nights
produces five session IDs. The correct way to report this number is 'distinct
sessions', or 'N pricing requests across M sessions'. It is not a headcount.

No IP addresses, user agents, or fingerprints are collected or derived.

Every function here is fail-safe: if the database is unreachable or the table has
not been created, tracking degrades to a no-op and logs a warning rather than
raising. Usage tracking must never take down the pricing pipeline.
"""

import logging
from datetime import datetime
from sqlalchemy import text
from src.data.db import Session, engine
from src.data.models import UsageEvent

logger = logging.getLogger(__name__)

# Only these event names are persisted. The /usage endpoint is unauthenticated so
# that the dashboard can call it, and this whitelist keeps arbitrary strings from
# being written into the table.
ALLOWED_EVENTS = ('session_start', 'price_request')


def ensure_usage_table():
    """
    Creates the usage_events table if it does not already exist.

    Called once on API startup so deployments that were provisioned before usage
    tracking existed pick up the new table without a manual migration. Only the
    usage_events table is touched; the existing signal tables are left alone.

    Returns:
        True if the table exists or was created, False if the database could not
        be reached.
    """

    try:
        UsageEvent.__table__.create(bind=engine, checkfirst=True)
        return True
    except Exception as exc:
        logger.warning('Usage table unavailable, tracking disabled: %s', exc)
        return False


def record_event(session_id, event, player=None, stat=None, bookmaker=None):
    """
    Writes a single usage event.

    Args:
        session_id: Random UUID minted per browser session by the dashboard (String).
        event: Event name, must be one of ALLOWED_EVENTS (String).
        player: Initialized to None. Player the request was for (String).
        stat: Initialized to None. Stat category the request was for (String).
        bookmaker: Initialized to None. Bookmaker selected for the request (String).

    Returns:
        True if the row was committed, False if it was skipped or the write failed.
        Never raises, so callers can treat tracking as fire-and-forget.
    """

    if not session_id or event not in ALLOWED_EVENTS:
        return False

    session = Session()
    try:
        session.add(UsageEvent(
            session_id=str(session_id)[:64],
            event=event,
            player=player,
            stat=stat,
            bookmaker=bookmaker,
            time_stamp=datetime.now()
        ))
        session.commit()
        return True
    # Tracking is best-effort. A failed write is logged and swallowed so a database
    # outage cannot break prop analysis for the user.
    except Exception as exc:
        session.rollback()
        logger.warning('Usage event not recorded: %s', exc)
        return False
    finally:
        session.close()


def usage_summary():
    """
    Aggregates the usage_events table into the numbers a developer would report.

    Returns:
        A dictionary containing distinct session and request counts, the date range
        covered, per-day activity, and the most requested players and stats. Returns
        a dictionary with 'available' set to False if the table is unreachable.
    """

    session = Session()
    try:
        totals = session.execute(text(
            'SELECT COUNT(DISTINCT session_id) AS sessions, '
            'COUNT(*) AS events, '
            'COUNT(*) FILTER (WHERE event = \'price_request\') AS price_requests, '
            'MIN(time_stamp) AS first_seen, '
            'MAX(time_stamp) AS last_seen, '
            'COUNT(DISTINCT DATE(time_stamp)) AS active_days '
            'FROM usage_events'
        )).mappings().first()

        # Sessions that actually priced a prop, as opposed to opening the dashboard
        # and leaving. This is the stricter and more defensible number of the two.
        engaged = session.execute(text(
            'SELECT COUNT(DISTINCT session_id) AS engaged_sessions '
            'FROM usage_events WHERE event = \'price_request\''
        )).mappings().first()

        per_day = session.execute(text(
            'SELECT DATE(time_stamp) AS day, '
            'COUNT(DISTINCT session_id) AS sessions, '
            'COUNT(*) FILTER (WHERE event = \'price_request\') AS price_requests '
            'FROM usage_events GROUP BY DATE(time_stamp) ORDER BY day'
        )).mappings().all()

        top_players = session.execute(text(
            'SELECT player, COUNT(*) AS requests FROM usage_events '
            'WHERE player IS NOT NULL GROUP BY player '
            'ORDER BY requests DESC, player ASC LIMIT 10'
        )).mappings().all()

        top_stats = session.execute(text(
            'SELECT stat, COUNT(*) AS requests FROM usage_events '
            'WHERE stat IS NOT NULL GROUP BY stat '
            'ORDER BY requests DESC, stat ASC LIMIT 10'
        )).mappings().all()

        return {
            'available': True,
            'metric_note': (
                'Counts distinct browser sessions, not people. Streamlit session '
                'state resets when the tab closes or the app sleeps, so one person '
                'across multiple nights registers as multiple sessions.'
            ),
            'distinct_sessions': totals['sessions'],
            'engaged_sessions': engaged['engaged_sessions'],
            'price_requests': totals['price_requests'],
            'total_events': totals['events'],
            'active_days': totals['active_days'],
            'first_seen': str(totals['first_seen']) if totals['first_seen'] else None,
            'last_seen': str(totals['last_seen']) if totals['last_seen'] else None,
            'per_day': [dict(row) | {'day': str(row['day'])} for row in per_day],
            'top_players': [dict(row) for row in top_players],
            'top_stats': [dict(row) for row in top_stats]
        }
    except Exception as exc:
        logger.warning('Usage summary unavailable: %s', exc)
        return {'available': False, 'error': str(exc)}
    finally:
        session.close()
