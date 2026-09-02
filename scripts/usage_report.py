"""
Prints the dashboard's usage numbers to the terminal.

Reads the usage_events table directly, so it works against a local database or a
hosted one depending on the DATABASE_URL environment variable.

Usage:
    python scripts/usage_report.py
    DATABASE_URL=postgresql://user:pass@host:5432/propvol python scripts/usage_report.py

The headline number is distinct sessions, not people. Streamlit clears session
state when the browser tab closes or the hosted app sleeps, so one person visiting
on five game nights registers as five sessions. Report it as 'N pricing requests
across M sessions', which is both accurate and more informative than a user count.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.db import DATABASE_URL
from src.data.usage import usage_summary


def main():
    summary = usage_summary()

    if not summary['available']:
        print('Could not read usage data from ' + DATABASE_URL)
        print('Error: ' + summary['error'])
        print()
        print('Check that the database is running and that DATABASE_URL points at it.')
        print('If the table does not exist yet, start the API once to create it, or run:')
        print('    psql $DATABASE_URL -f src/db/schema.sql')
        return 1

    print('Monte Carlo NBA Prop Pricing Engine, usage report')
    print('Database: ' + DATABASE_URL)
    print()

    if summary['total_events'] == 0:
        print('No usage recorded yet.')
        return 0

    print('Distinct sessions:        ' + str(summary['distinct_sessions']))
    print('Sessions that priced:     ' + str(summary['engaged_sessions']))
    print('Pricing requests:         ' + str(summary['price_requests']))
    print('Active days:              ' + str(summary['active_days']))
    print('First activity:           ' + str(summary['first_seen']))
    print('Last activity:            ' + str(summary['last_seen']))
    print()
    print('Reportable as: ' + str(summary['price_requests']) + ' pricing requests across ' +
          str(summary['distinct_sessions']) + ' distinct sessions.')
    print('Counts sessions, not people. See the module docstring before quoting this.')

    if summary['per_day']:
        print()
        print('By day:')
        print('  ' + 'date'.ljust(14) + 'sessions'.rjust(10) + 'requests'.rjust(10))
        for row in summary['per_day']:
            print('  ' + str(row['day']).ljust(14) + str(row['sessions']).rjust(10) + str(row['price_requests']).rjust(10))

    if summary['top_players']:
        print()
        print('Most requested players:')
        for row in summary['top_players']:
            print('  ' + str(row['player']).ljust(28) + str(row['requests']).rjust(5))

    if summary['top_stats']:
        print()
        print('Most requested stats:')
        for row in summary['top_stats']:
            print('  ' + str(row['stat']).ljust(28) + str(row['requests']).rjust(5))

    return 0


if __name__ == '__main__':
    sys.exit(main())
