from application import BLOB_CONNECTION_STRING
from application.constants import *
from application.user import (
    check_code,
    email_in_db,
    get_address_from_email,
    get_password_from_email,
    get_username_from_email,
    hash_password,
    insert_jti_in_blacklist,
    save_to_db,
    save_to_db_temp,
    update_password,
    username_in_db
)
from azure.storage.blob import BlobClient
from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_raw_jwt,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies
)
from flask.wrappers import Response
from typing import Union
from werkzeug.security import safe_str_cmp
import re


bp = Blueprint('auth', __name__, url_prefix='')
REGEX_USERNAME = "^[a-zA-Z0-9]*$"


@bp.route('/login', methods=('GET', 'POST'))
def login() -> Union[str, Response]:
    session.clear()
    session.pop('_flashes', None)
    if request.method == 'POST' and 'login' in request.form:
        error = None
        if 'email' not in request.form:
            error = "Email is required."
        if 'password' not in request.form:
            error = "Password is required."

        if error is None:
            email = request.form['email']
            password = hash_password(request.form['password'])
            if ' ' in email or '@' not in email:
                error = "Please enter a valid email."

            if error is None:
                if not email_in_db(email):
                    error = f"Account for {email} does not exist. Try to register."
                if error is None:
                    if safe_str_cmp(password, get_password_from_email(email)):
                        if get_address_from_email(email) is not None:
                            session["installed"] = True
                        response = make_response(redirect(url_for('main.gallery')))
                        username = get_username_from_email(email)
                        access_token = create_access_token(identity={"email": email, "username": username})
                        refresh_token = create_refresh_token(identity={"email": email, "username": username})
                        set_access_cookies(response, access_token)
                        set_refresh_cookies(response, refresh_token)
                        return response
                    else:
                        error = "Wrong credentials."
        flash(error)
    return render_template('auth/login.html')


@bp.route('/logout')
@jwt_required
def logout() -> Union[str, Response]:
    jti = get_raw_jwt()["jti"]
    insert_jti_in_blacklist(jti)
    session.clear()
    response = make_response(redirect(url_for('auth.login')))
    response.set_cookie('refresh_token_cookie', '', expires=0)
    response.set_cookie('session', '', expires=0)
    return response


@bp.route('/register', methods=('GET', 'POST'))
def register() -> str:
    session.clear()
    session.pop('_flashes', None)
    if request.method == 'POST' and 'register' in request.form:
        error = None
        if 'username' not in request.form:
            error = "Username is required."
        if 'password' not in request.form:
            error = "Password is required."
        if 'email' not in request.form:
            error = "Email is required."
        if 'fullname' not in request.form:
            error = "Fullname is required."

        if error is None:
            username = request.form['username']
            password = hash_password(request.form['password'])
            email = request.form['email']
            fullname = request.form['fullname']
            if ' ' in email or '@' not in email:
                error = "Please enter a valid email."

            if len(request.form['fullname']) > 20 or len(request.form['fullname']) < 1:
                error = "Fullname should be with a maximum of 20 characters and minimum of 1."
            if not bool(re.match(REGEX_FULLNAME, request.form['fullname'])):
                error = "Fullname should contains only letters, numbers and spaces"
            if len(request.form['username']) > 13 or len(request.form['username']) < 1:
                error = "Username should be with a maximum of 13 characters and minimum of 1."
            if not bool(re.match(REGEX_USERNAME, request.form['username'])):
                error = "Username should contains only letters or numbers"
            if len(request.form['password']) < 6:
                error = "Password should contains at least 6 characters."
            if error is None:
                if username_in_db(username):
                    error = f"Username {username} already exist, try an other one."
                if email_in_db(email):
                    error = f"We already have an account for {email}."
                if error is None:
                    session['email'] = email
                    save_to_db_temp("Verification Code", email, username=username, password=password, fullname=fullname)
                    return redirect(url_for('auth.registration_validation'))
        flash(error)
    return render_template('auth/register.html')


@bp.route('/registration_validation', methods=('GET', 'POST'))
def registration_validation() -> Union[str, Response]:
    session.pop('_flashes', None)
    if request.method == 'POST':
        email = session.get('email')
        error = None
        if 'code' not in request.form:
            error = "Code is required."
        if email is None:
            error = "Email is required in Session."
        try:
            int(request.form['code'])
        except ValueError:
            error = "Enter a number."

        if error is None:
            code = int(request.form['code'])
            if not check_code(code, email):
                error = "Code is wrong."

            if error is None:
                session.clear()
                if get_address_from_email(email) is not None:
                    session["installed"] = True
                save_to_db(email)
                username = get_username_from_email(email)
                default_client = BlobClient.from_connection_string(BLOB_CONNECTION_STRING, PROFILE_PICTURES_CONTAINER,
                                                                   'default-profile.png')
                data = default_client.download_blob().readall()
                user_client = BlobClient.from_connection_string(BLOB_CONNECTION_STRING, PROFILE_PICTURES_CONTAINER,
                                                                f"{username}.png")
                user_client.upload_blob(data, overwrite=True)
                response = make_response(redirect(url_for('main.gallery')))
                access_token = create_access_token(identity={"email": email, "username": username})
                refresh_token = create_refresh_token(identity={"email": email, "username": username})
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
                return response
        flash(error)
    return render_template('auth/registration_validation.html')


@bp.route('/forgot_password', methods=('GET', 'POST'))
def forgot_password() -> str:
    session.clear()
    session.pop('_flashes', None)
    if request.method == 'POST' and 'forgot' in request.form:
        error = None
        if 'email' not in request.form:
            error = "Email is required."
        if error is None:
            email = request.form['email']
            if ' ' in email or '@' not in email:
                error = "Please enter a valid email."

            if error is None:
                if not email_in_db(email):
                    error = f"Account for {email} does not exist"
                if error is None:
                    session['email'] = email
                    save_to_db_temp("Reset Password", email)
                    return redirect(url_for('auth.reset_password'))
        flash(error)
    return render_template('auth/forgot_password.html')


@bp.route('/reset_password', methods=('GET', 'POST'))
def reset_password() -> Union[str, Response]:
    session.pop('_flashes', None)
    if request.method == 'POST' and 'reset' in request.form:
        error = None
        if 'code' not in request.form:
            error = "Code is required."
        if 'password' not in request.form:
            error = "Password is required."
        email = session.get('email')
        if email is None:
            error = "Email is required in Session."
        try:
            int(request.form['code'])
        except ValueError:
            error = "Enter a number."

        if error is None:
            password = hash_password(request.form['password'])
            code = int(request.form['code'])
            if not check_code(code, email):
                error = "Code is wrong."

            if error is None:
                session.clear()
                if get_address_from_email(email) is not None:
                    session["installed"] = True
                update_password(email, password)
                response = make_response(redirect(url_for('main.gallery')))
                username = get_username_from_email(email)
                access_token = create_access_token(identity={"email": email, "username": username})
                refresh_token = create_refresh_token(identity={"email": email, "username": username})
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
                return response
        flash(error)
    return render_template('auth/reset_password.html')
