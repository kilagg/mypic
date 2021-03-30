from application.auction import manage_auction
from application.buy import manage_buy
from application.constants import *
from application.market import (
    build_image_favorites,
    cancel_resale,
    create_new_image,
    create_resale,
    download_blob_data,
    get_image_from_address,
    get_new_images,
    get_resale
)
from application.user import (
    is_follow,
    follow,
    unfollow,
    get_address_from_email,
    get_address_from_username,
    get_followers_from_username,
    get_fullname_from_email,
    get_fullname_from_username,
    get_nsfw_from_email,
    get_is_public_from_username,
    get_password_from_email,
    get_profile_picture_extension_from_email,
    get_profile_picture_extension_from_username,
    get_stars_from_follower,
    get_username_of_resale,
    hash_password,
    update_address,
    update_fullname,
    update_nsfw,
    update_password,
    update_profile_picture
)
from datetime import datetime, timedelta
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from flask_jwt_extended import get_jwt_identity, jwt_required
from joblib import delayed, Parallel
from werkzeug.utils import secure_filename
from werkzeug.security import safe_str_cmp
import json
import multiprocessing
import re

bp = Blueprint('main', __name__, url_prefix='')
REGEX_TITLE_IMAGE = "^[a-zA-Z0-9 ]*$"


@bp.route('/account', methods=('GET', 'POST'))
@jwt_required
def account() -> str:
    email = get_jwt_identity()['email']
    username = get_jwt_identity()['username']
    fullname = get_fullname_from_email(email)
    pp_extension = get_profile_picture_extension_from_email(email)
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    followers = get_followers_from_username(username)
    nsfw = get_nsfw_from_email(email)
    user = {'username': username,
            'fullname': fullname,
            'nsfw': nsfw,
            'profile_picture': f"data:{pp_extension};base64,{profile_picture}",
            'followers': str(followers)}
    if request.method == 'POST':
        if 'update_parameters' in request.form:
            if 'fullname' in request.form and request.form['fullname'] != fullname:
                error = None
                if len(request.form['fullname']) > 20 or len(request.form['fullname']) < 1:
                    error = "Fullname should be with a maximum of 20 characters and minimum of 1."
                if not bool(re.match(REGEX_FULLNAME, request.form['fullname'])):
                    error = "Fullname should contains only letters, numbers and spaces"
                if error is None:
                    update_fullname(email, request.form['fullname'])
                flash(error)
                return error

            if 'nsfw' in request.form and (request.form['nsfw'] == 'on') != nsfw:
                new_nsfw = int(request.form['nsfw'] == 'on')
                update_nsfw(email, new_nsfw)

            if 'old_password' in request.form and 'new_password' in request.form and request.form['new_password'] != '':
                old_password = hash_password(request.form['old_password'])
                new_password = hash_password(request.form['new_password'])
                error = None
                if len(request.form['new_password']) < 6:
                    error = "Password should contains at least 6 characters."
                if not safe_str_cmp(old_password, get_password_from_email(email)):
                    error = "Wrong Password."
                if error is None:
                    update_password(email, new_password)
                return error
            return render_template('app/account.html', user=user)

        if 'update_profile_picture' in request.form:
            error = None
            if 'file' not in request.files:
                error = "Image is required."
            if error is None:
                file = request.files['file']
                extension = DICTIONARY_FORMAT[secure_filename(file.filename).split('.')[-1].lower()]
                update_profile_picture(username, file, extension)
                message = "Profile Picture was updated."
                return message
            return error
    return render_template('app/account.html', user=user)


@bp.route('/favorites', methods=('GET', 'POST'), endpoint='v1')
@bp.route('/feed', methods=('GET', 'POST'), endpoint='v2')
@jwt_required
def feed() -> str:
    page = 'feed' if request.endpoint == 'main.v2' else 'favorites'
    if request.method == 'POST':
        if "more" in request.form:
            email = get_jwt_identity()['email']
            username = get_jwt_identity()['username']
            follower = None if request.endpoint == 'main.v2' else username
            if request.form["more"] == "new":
                data_new_images = get_new_images(session.get(f'{page}_number_new'), email=email, follower=follower)
                session[f'{page}_number_new'] = session.get(f'{page}_number_new') + 1
                return json.dumps({"pictures": data_new_images})

            if request.form["more"] == "resale":
                resale_images = get_resale(session.get(f'{page}_number_resale'), email=email, follower=follower)
                session[f'{page}_number_resale'] = session.get(f'{page}_number_resale') + 1
                return json.dumps({"pictures": resale_images})

        if 'type' in request.form:
            if (request.form['type'] == 'new'
                    or request.form['type'] == 'validate_new'
                    or request.form['type'] == 'error_new'):
                return manage_auction(request.form, get_jwt_identity()['username'])

            if request.form['type'] == 'resale' or request.form['type'] == 'validate_resale':
                return manage_buy(request.form, get_jwt_identity()['username'])
        return "no api"
    session[f'{page}_number_new'] = 0
    session[f'{page}_number_resale'] = 0
    return render_template(f'app/{page}.html')


@bp.route('/gallery', methods=('GET', 'POST'))
@jwt_required
def gallery() -> str:
    if request.method == 'POST':
        email = get_jwt_identity()['email']
        address = get_address_from_email(email)
        username = get_jwt_identity()['username']
        if "more" in request.form:
            if request.form["more"] == "my-pics":
                data_my_gallery = get_image_from_address(address, session.get('number_my_gallery'), my=True)
                session['number_my_gallery'] = session.get('number_my_gallery') + 1
                return json.dumps({"pictures": data_my_gallery})

            if request.form["more"] == "my-sell":
                data_new_images = get_new_images(session.get('number_my_new_image'), username=username, my=True)
                session['number_my_new_image'] = session.get('number_my_new_image') + 1
                return json.dumps({"pictures": data_new_images})

            if request.form["more"] == "my-resale":
                resale_images = get_resale(session.get('number_my_resale'), username=username, my=True)
                session['number_my_resale'] = session.get('number_my_resale') + 1
                return json.dumps({"pictures": resale_images})

        if 'type' in request.form:
            if request.form['type'] == 'cancel':
                error = None
                if 'token_id' not in request.form:
                    error = "Token ID is required."
                try:
                    int(request.form['token_id'])
                except ValueError:
                    error = "Enter an integer for token ID."

                if error is None:
                    token_id = int(request.form['token_id'])
                    if get_username_of_resale(token_id) != username:
                        error = "You are not the seller of this token, you cannot cancel it."
                    if error is None:
                        cancel = cancel_resale(token_id)
                        if cancel:
                            return redirect(url_for('main.gallery'))
                        else:
                            return "Issue in Cancel, retry"
                return error

            if request.form['type'] == 'sell':
                error = None
                if 'txID' not in request.form:
                    error = 'Transaction ID is required.'
                if 'price' not in request.form:
                    error = "Price is required."
                if 'token_id' not in request.form:
                    error = "Token ID is required."
                try:
                    int(request.form['price'])
                except ValueError:
                    error = "Enter an integer for price."
                try:
                    int(request.form['token_id'])
                except ValueError:
                    error = "Enter an integer for token ID."
                if error is None:
                    price = int(request.form['price'])
                    token_id = int(request.form['token_id'])
                    tx_id = request.form['txID']
                    create_resale(username, token_id, price, tx_id)
                    return redirect(url_for('main.gallery'))
                return error
        return "No api for this POST request"
    session['number_my_gallery'] = 0
    session['number_my_new_image'] = 0
    session['number_my_resale'] = 0
    return render_template("app/gallery.html")


@bp.route('/list_favorites', methods=('GET', 'POST'))
@jwt_required
def list_favorites():
    username = get_jwt_identity()['username']
    stars = get_stars_from_follower(username)
    num_cores = multiprocessing.cpu_count()
    users = Parallel(n_jobs=num_cores)(delayed(build_image_favorites)(star) for star in stars)
    return render_template("app/list_favorites.html", users=users)


@bp.route('/gallery/<username>', methods=('GET', 'POST'))
@jwt_required
def gallery_navigation(username: str) -> str:
    if username == get_jwt_identity()['username']:
        return redirect(url_for('main.gallery'))
    if request.method == 'POST':
        is_public = get_is_public_from_username(username)
        if "more" in request.form:
            address = get_address_from_username(username)
            if request.form["more"] == "my-pics":
                data_my_gallery = get_image_from_address(address, session.get('number_other_gallery'), is_public)
                session['number_other_gallery'] = session.get('number_other_gallery') + 1
                return json.dumps({"pictures": data_my_gallery})

            if request.form["more"] == "my-sell":
                print("ici", username)
                data_new_images = get_new_images(session.get('number_other_new_image'), username=username)
                print("longueur", len(data_new_images))
                session['number_other_new_image'] = session.get('number_other_new_image') + 1
                return json.dumps({"pictures": data_new_images})

            if request.form["more"] == "my-resale":
                resale_images = get_resale(session.get('number_other_resale'), username=username)
                session['number_other_resale'] = session.get('number_other_resale') + 1
                return json.dumps({"pictures": resale_images})

        if 'type' in request.form:
            if (request.form['type'] == 'new'
                    or request.form['type'] == 'validate_new'
                    or request.form['type'] == 'error_new'):
                return manage_auction(request.form, get_jwt_identity()['username'])

            if request.form['type'] == 'resale' or request.form['type'] == 'validate_resale':
                return manage_buy(request.form, get_jwt_identity()['username'])

            if request.form['type'] == 'follow':
                follow(get_jwt_identity()['username'], username)
                return "Follow done"

            if request.form['type'] == 'unfollow':
                unfollow(get_jwt_identity()['username'], username)
                return "Unfollow done"

    session['number_other_gallery'] = 0
    session['number_other_new_image'] = 0
    session['number_other_resale'] = 0
    pp_extension = get_profile_picture_extension_from_username(username)
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    followers = get_followers_from_username(username)
    fullname = get_fullname_from_username(username)
    is_follow_int = int(is_follow(get_jwt_identity()['username'], username))
    user = {'username': username,
            'profile_picture': f"data:{pp_extension};base64,{profile_picture}",
            'followers': str(followers),
            'fullname': fullname,
            'is_follow': is_follow_int}
    return render_template("app/gallery_navigation.html", user=user)


@bp.route('/create', methods=('GET', 'POST'))
@jwt_required
def market() -> str:
    print(request.form)
    if request.method == 'POST' and 'create' in request.form:
        error = None
        if 'file' not in request.files:
            error = "File is required."
        if 'title' not in request.form:
            error = "Title is required."
        if 'price' not in request.form:
            error = "Price is required."
        if 'duration' not in request.form:
            error = "Duration is required."
        try:
            int(request.form['price'])
        except ValueError:
            error = "Enter an integer for price."
        if int(request.form['price']) < 1:
            error = "Price should be higher that 1 Algo."
        try:
            int(request.form['duration'])
        except ValueError:
            error = "Enter an integer for duration."
        if int(request.form['duration']) > 48 or int(request.form['duration']) < 1:
            error = "Choose a duration between 1 and 48 hours"
        if len(request.form['title']) > 13:
            error = "Title should be with a maximum of 13 characters."
        if not bool(re.match(REGEX_TITLE_IMAGE, request.form['title'])):
            error = "Title should contains only letters, numbers and spaces"
        if secure_filename(request.files['file'].filename).split('.')[-1].lower() not in DICTIONARY_FORMAT:
            error = f"We only accept format in : {','.join(list(DICTIONARY_FORMAT.keys()))}"

        if error is None:
            username = get_jwt_identity()['username']
            file = request.files['file']
            title = request.form['title']
            price = int(request.form['price'])
            end_date = datetime.utcnow() + timedelta(hours=int(request.form['duration']))
            public = 0 if 'private' in request.form else 1
            nsfw = 1 if 'nsfw' in request.form else 0
            create_new_image(username, file, title, price, end_date, public, nsfw)
            return redirect(url_for('main.gallery'))
        flash(error)
    return render_template('app/create.html')


@bp.route('/wallet_installed', methods=('GET', 'POST'))
@jwt_required
def wallet_installed():
    email = get_jwt_identity()['email']
    error = None
    if 'wallet' not in request.form:
        error = "Wallet is required."

    if error is None:
        address = json.loads(request.form['wallet'])[0]['address']
        update_address(email, address)
        session["installed"] = True
        return "Address updated."
    return error
