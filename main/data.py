from datetime import datetime, timedelta
import random

def make_transactions(start_date, end_date):
    """
    Build one transaction per day at 9:00, 12:00, and 16:00,
    with a gentle trend plus random noise.
    """
    txns = []
    current = start_date
    day_id = 1

    # parameters for the trend lines
    # morning_amt = a_morning * day_count + b_morning + noise
    a_morning, b_morning = 1.5, 200
    a_noon,    b_noon    = 0,   300
    a_after,   b_after   = -1.5, 500

    while current <= end_date:
        day_count = (current - start_date).days

        # morning
        amt_m = a_morning * day_count + b_morning \
                + random.gauss(0, 5)    # σ=5
        txns.append({
            'id': day_id,
            'date': datetime(current.year, current.month, current.day, 9, 0),
            'amount': round(amt_m, 2)
        })
        day_id += 1

        # noon
        amt_n = a_noon * day_count + b_noon \
                + random.gauss(0, 4)    # σ=2
        txns.append({
            'id': day_id,
            'date': datetime(current.year, current.month, current.day, 12, 0),
            'amount': round(amt_n, 2)
        })
        day_id += 1

        # afternoon
        amt_a = a_after * day_count + b_after \
                + random.gauss(0, 5)    # σ=5
        txns.append({
            'id': day_id,
            'date': datetime(current.year, current.month, current.day, 16, 0),
            'amount': round(amt_a, 4)
        })
        day_id += 1

        current += timedelta(days=1)

    return txns

# Usage:
transactions = make_transactions(
    start_date=datetime(2024,1,1),
    end_date  =datetime(2024,12,31)
)