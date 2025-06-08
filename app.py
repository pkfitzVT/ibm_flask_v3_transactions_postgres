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


# Update operation: Display edit transaction form
# Route to handle the editing of an existing transaction
@app.route("/edit/<int:transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    # Check if the request method is POST (form submission)
    if request.method == 'POST':
        # Extract the updated values from the form fields
        date = request.form['date']  # Get the 'date' field value from the form
        amount = float(request.form['amount'])  # Get the 'amount' field value from the form and convert it to a float

        # Find the transaction with the matching ID and update its values
        for transaction in transactions:
            if transaction['id'] == transaction_id:
                transaction['date'] = date  # Update the 'date' field of the transaction
                transaction['amount'] = amount  # Update the 'amount' field of the transaction
                break  # Exit the loop once the transaction is found and updated

        # Redirect to the transactions list page after updating the transaction
        return redirect(url_for("get_transactions"))

    # If the request method is GET, find the transaction with the matching ID and render the edit form
    for transaction in transactions:
        if transaction['id'] == transaction_id:
            # Render the edit form template and pass the transaction to be edited
            return render_template("edit.html", transaction=transaction)

    # If the transaction with the specified ID is not found, handle this case (optional)
    return {"message": "Transaction not found"}, 404

# Delete operation: Delete a transaction
# Route to handle the deletion of an existing transaction
@app.route("/delete/<int:transaction_id>")
def delete_transaction(transaction_id):
    # Find the transaction with the matching ID and remove it from the list
    for transaction in transactions:
        if transaction['id'] == transaction_id:
            transactions.remove(transaction)  # Remove the transaction from the transactions list
            break  # Exit the loop once the transaction is found and removed

    # Redirect to the transactions list page after deleting the transaction
    return redirect(url_for("get_transactions"))



# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5001)