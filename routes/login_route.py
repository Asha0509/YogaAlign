from flask import Blueprint, render_template, request, session, redirect, url_for
from models import LoginModel
from pydantic import ValidationError
from db_services import validate_user

login_bp = Blueprint('login', __name__)

@login_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            credentials = LoginModel(email=email, password=password)
        except ValidationError as e:
            return render_template("signin.html", error=e.errors()[0]['msg'])

        user = validate_user(credentials.email, credentials.password)
        if user:
            session['user_id'] = user[0]
            session['user'] = user[1] 
            return redirect(url_for('video.dashboard')) 
        else:
            return render_template('signin.html', error="Invalid email or password.")
    return render_template('signin.html')
