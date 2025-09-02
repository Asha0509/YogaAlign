from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import UserModel
from db_services import add_user
from pydantic import ValidationError

signup_bp = Blueprint('signup', __name__)

@signup_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            user_data = UserModel(
                name=request.form['name'],
                email=request.form['email'],
                password=request.form['password'],
                confirm_password=request.form['confirm_password']
            )

            add_user(user_data.name, user_data.email, user_data.password)
            flash("Signup successful! Please login.")
            return redirect(url_for('login.signin'))

        except ValidationError as ve:
            error_msg = ve.errors()[0]['msg']
            return render_template('signup.html', error=error_msg)
        except ValueError as ve:
            return render_template('signup.html', error=str(ve))
        except Exception as e:
            return render_template('signup.html', error=f"Something went wrong: {str(e)}")

    return render_template('signup.html')
