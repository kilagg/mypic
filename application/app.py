from application import app, auth_bp, main_bp, help_bp
from application.user import jti_in_blacklist
from datetime import datetime, timedelta, timezone
from flask import flash, redirect, url_for
from flask_jwt_extended import create_access_token, get_jwt_identity, get_raw_jwt, JWTManager, set_access_cookies


app.register_blueprint(auth_bp.bp)
app.register_blueprint(main_bp.bp)
app.register_blueprint(help_bp.bp)
# TODO : Change secret key, remove debug
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.debug = True
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(hours=12)
jwt = JWTManager(app)


@app.route("/")
def hello():
    return redirect(url_for('main.gallery'))


@jwt.expired_token_loader
def my_expired_token_callback():
    return redirect(url_for('auth.login'))


@jwt.token_in_blacklist_loader
def my_token_in_blacklist_callback(jwt_payload):
    jti = jwt_payload["jti"]
    return jti_in_blacklist(jti)


@jwt.unauthorized_loader
def my_unauthorized_callback(callback):
    flash(callback)
    return redirect(url_for('auth.login'))


@app.after_request
def refresh_expiring_jwt(response):
    try:
        # TODO : check refresh token
        exp_timestamp = get_raw_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=10))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        return response
