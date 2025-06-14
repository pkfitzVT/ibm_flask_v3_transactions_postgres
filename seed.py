"""
Seed the `transactions` table with demo data from `data.py` under a single demo user.
Usage:
    python seed.py
"""
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from main.data import transactions as demo_txns
from models import Transaction, User


def seed():
    app = create_app()
    with app.app_context():
        # 1) Create or fetch demo user
        demo_user = User.query.filter_by(name="demo_user").first()
        if not demo_user:
            demo_user = User(
                name="demo_user", password_hash=generate_password_hash("password123")
            )
            db.session.add(demo_user)
            db.session.commit()

        # 2) Build mappings for bulk insert
        mappings = []
        for t in demo_txns:
            # data.py uses key 'date', rename to model's date_time
            dt = t.get("dateTime") or t.get("date")
            mappings.append(
                {
                    "user_id": demo_user.id,
                    "date_time": dt,
                    "amount": t["amount"],
                    "description": None,
                }
            )

        # 3) Insert transactions
        db.session.bulk_insert_mappings(Transaction, mappings)
        db.session.commit()

        print(f"Seeded {len(mappings)} transactions for user_id={demo_user.id}")


if __name__ == "__main__":
    seed()
