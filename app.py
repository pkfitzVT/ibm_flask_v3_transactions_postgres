# Import libraries
from flask import Flask, redirect, request, render_template, url_for
from datetime import datetime

# Instantiate Flask functionality
app = Flask(__name__)


# Sample data
transactions = [
    {'id': 1, 'date': '2023-06-01', 'amount': 100},
    {'id': 2, 'date': '2023-06-02', 'amount': -200},
    {'id': 3, 'date': '2023-06-03', 'amount': 300}
]
# Read operation: List all transactions
@app.route("/")
def get_transactions():
    return render_template("transactions.html", transactions=transactions)

# Create operation
@app.route("/add", methods=["GET", "POST"])
def add_transaction():
    if request.method == 'POST':
        try:
            # Try to parse date to ensure it is valid
            date_str = request.form['date']
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = parsed_date.strftime("%Y-%m-%d")  # Save in consistent format

            amount = float(request.form['amount'])

            transaction = {
                'id': len(transactions) + 1,
                'date': formatted_date,
                'amount': amount
            }

            transactions.append(transaction)
            return redirect(url_for("get_transactions"))

        except ValueError:
            # Invalid date format or amount → show error (for now, print)
            return "Invalid date format. Please use YYYY-MM-DD.", 400

    return render_template("form.html")

# Update operation
@app.route("/edit/<int:transaction_id>")
def edit_transaction(transaction_id):
    return f"Edit page for transaction {transaction_id}"
# Delete operation
@app.route("/delete/<int:transaction_id>")
def delete_transaction(transaction_id):
    # For now, just show which transaction would be deleted
    return f"Delete transaction {transaction_id} (Not implemented yet)"


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5001)
