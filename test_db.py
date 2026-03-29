import sqlalchemy
url = "postgresql://admin:secret@localhost:5433/cs432_db"
engine = sqlalchemy.create_engine(url)
with engine.connect() as conn:
    print(conn.execute(sqlalchemy.text("SELECT count(*) FROM pg_stat_activity WHERE datname='cs432_db'")).scalar())
    conn.execute(sqlalchemy.text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='cs432_db' AND pid <> pg_backend_pid();"))
    conn.commit()
    conn.execute(sqlalchemy.text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    conn.commit()
print("Done")
