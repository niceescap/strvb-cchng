import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

load_dotenv(Path.home() / "coach" / ".env", override=True)
url = os.environ["DATABASE_URL"]
assert make_url(url).database == "coach_proto", "garde : base inattendue"

engine = create_engine(url)
with engine.connect() as c:
    for t in ["coach_users", "coach_activities", "coach_artifacts"]:
        print(f"\n== {t}")
        rows = c.execute(text(
            "SELECT column_name, data_type, column_default, is_nullable "
            "FROM information_schema.columns WHERE table_schema='public' AND table_name=:t "
            "ORDER BY ordinal_position"), {"t": t})
        for r in rows:
            print("  ", " | ".join(str(x) for x in r))
        print("   lignes :", c.execute(text(f"SELECT count(*) FROM {t}")).scalar())

    print("\n== tables de crédit")
    for t in ["credit_ledger", "model_pricing", "coupons"]:
        print(f"  {t} :", c.execute(text("SELECT to_regclass(:t)"), {"t": t}).scalar())

    print("\n== migrations 0002 (colonnes)")
    for col in ["compact_json", "best_json", "device_watts"]:
        print(f"  {col} :", c.execute(text(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name='coach_activities' AND column_name=:c"), {"c": col}).scalar())

    print("\n== credit_tokens")
    has = c.execute(text(
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_name='coach_users' AND column_name='credit_tokens'")).scalar()
    if has:
        print("   non nul :", c.execute(text("SELECT count(credit_tokens) FROM coach_users")).scalar())
        print("   différent de zéro :", c.execute(text(
            "SELECT count(*) FROM coach_users WHERE credit_tokens <> 0")).scalar())
    else:
        print("   colonne absente")
