"""
Shared database engine and session factory.

Previously the engine was constructed inline in src/api/main.py with a hardcoded
connection string, which meant the DATABASE_URL supplied by docker-compose (and by
any hosted deployment) was ignored. Centralizing it here lets the API, the usage
tracker, and the offline reporting script all talk to the same database.

The default preserves the original local connection string so existing local
setups behave exactly as before.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/propvol')

# A bounded connect timeout keeps the API from hanging indefinitely when the
# database is unreachable (for example when the dashboard is running but Postgres
# is not). Only Postgres drivers accept connect_timeout.
if DATABASE_URL.startswith('postgres'):
    engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 5})
else:
    engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)
