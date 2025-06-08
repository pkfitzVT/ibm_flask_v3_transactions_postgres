# Import libraries
from flask import Flask, redirect, request, render_template, url_for


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
@app.route("/add")
def add_transaction():
    return "Add Transaction page (Not implemented yet)"

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
