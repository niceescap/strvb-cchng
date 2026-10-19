#!/usr/bin/env python3
"""Crée un coupon unique. Le code clair est affiché une seule fois ; seul son HMAC est stocké."""
import hashlib
import hmac
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
db_name = make_url(os.environ.get('DATABASE_URL', '')).database
if db_name != 'coach_proto':
    sys.exit(f"Refus : base '{db_name}' inattendue, attendu coach_proto")

MAX_MICRO_USD = 50_000_000  # garde-fou : 50 $ maximum par coupon


def main():
    secret = os.environ.get("COUPON_HMAC_SECRET", "")
    if len(secret) < 32:
        sys.exit("COUPON_HMAC_SECRET absent ou trop court dans .env")

    raw = input("Valeur du coupon en dollars (ex. 5) : ").strip().replace(",", ".")
    try:
        usd = Decimal(raw)
    except InvalidOperation:
        sys.exit("Valeur invalide.")
    micro = int(usd * 1_000_000)
    if micro <= 0 or micro > MAX_MICRO_USD:
        sys.exit("Valeur hors limites : entre 0,01 $ et 50 $.")

    days_raw = input("Validité en jours (défaut 7) : ").strip() or "7"
    if not days_raw.isdigit() or not (1 <= int(days_raw) <= 365):
        sys.exit("Validité invalide.")
    expires = datetime.now(timezone.utc) + timedelta(days=int(days_raw))

    confirm = input(f"Créer un coupon de {usd} $ valable jusqu'au {expires:%Y-%m-%d} ? (oui/non) : ")
    if confirm.strip().lower() != "oui":
        sys.exit("Annulé.")

    code = secrets.token_urlsafe(18)
    digest = hmac.new(secret.encode(), code.encode(), hashlib.sha256).hexdigest()

    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO coupons (code_hash, amount_micro_usd, expires_at, max_redemptions, active)
                    VALUES (:h, :m, :e, 1, true)"""),
            {"h": digest, "m": micro, "e": expires},
        )

    print(f"\nCoupon créé : {usd} $ valable jusqu'au {expires:%Y-%m-%d}")
    print(f"Code (affiché une seule fois, à noter maintenant) : {code}\n")


if __name__ == "__main__":
    main()
