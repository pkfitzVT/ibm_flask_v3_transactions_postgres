# auth/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash




import secrets

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

# In-memory for now
users = []

@auth_bp.route('/')
def splash():
    return render_template('splash.html')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        email = request.form['email']
        pw_hash = generate_password_hash(request.form['password'])
        users.append({'id':len(users)+1, 'email':email, 'pw_hash':pw_hash})
        flash('Registered—please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form['email']; pw = request.form['password']
        user = next((u for u in users if u['email']==email), None)
        if user and check_password_hash(user['pw_hash'], pw):
            session['user_id'] = user['id']
            return redirect(url_for('main.get_transactions'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

