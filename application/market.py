from application import BLOB_CONNECTION_STRING, SWARM_URL_NODE
from application.constants import *
from application.sql_manager import SqlManager
from application.smart_contract import (
    list_account_assets,
    mint_official_nft,
    transfer_nft_to_user,
    wait_for_confirmation
)
from application.user import (
    get_address_of_resale,
    get_fullname_from_username,
    get_profile_picture_extension_from_username,
    get_username_from_email
)
from azure.storage.blob import BlobClient
from datetime import datetime
from joblib import delayed, Parallel
from pandas.core.series import Series
from PIL import Image, ImageFilter
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import base64
import io
import json
import multiprocessing
import requests


BLURRY_IMAGES_CONTAINER = "imagesblurry"
IMAGES_CONTAINER = "images"
NUMBER_PRINT_IMAGE = 9


def build_image_favorites(star: str) -> dict:
    fullname = get_fullname_from_username(star)
    pp_extension = get_profile_picture_extension_from_username(star)
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{star.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    image = {'username': star,
             'fullname': fullname,
             'profile_picture': f"data:{pp_extension};base64,{profile_picture}"}
    return image


def build_image_gallery(row: Series, my: bool) -> dict:
    container = IMAGES_CONTAINER if row['is_public'] or my else BLURRY_IMAGES_CONTAINER
    extension = row['extension']
    image_path = f"{row['username'].lower()}/{row['swarm_hash']}.{extension}"
    pp_extension = row['profile_picture_extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{row['username'].lower()}.{pp_extension}"
    image = {'username': row['username'],
             'extention': f"{row['extension']}",
             'uri': f"data:image/{extension};base64,{download_blob_data(container, image_path)}",
             'token_id': row['token_id'],
             'title': row['title'],
             'pp': f"data:image/{pp_extension};base64,{download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)}"}
    return image


def build_new_image(row: Series, my: bool) -> dict:
    container = IMAGES_CONTAINER if row['is_public'] or my else BLURRY_IMAGES_CONTAINER
    extension = row['extension']
    image_path = f"{row['username'].lower()}/{row['swarm_hash']}.{extension}"
    pp_extension = row['profile_picture_extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{row['username'].lower()}.{pp_extension}"
    image = {'username': row['username'],
             'title': row['title'],
             'extension': f"{extension}",
             'uri': f"data:image/{extension};base64,{download_blob_data(container, image_path)}",
             'token_id': row['token_id'],
             'price': row['current_price'],
             'min_price': int(row['current_price'] * 1.1) + 1,
             'end_date': row['end_date'].strftime("%Y-%m-%d %H:%M:%S"),
             'pp': f"data:image/{pp_extension};base64,{download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)}"}
    return image


def build_resale_images(row: Series, my: bool) -> dict:
    container = IMAGES_CONTAINER if row['is_public'] or my else BLURRY_IMAGES_CONTAINER
    extension = row['extension']
    image_path = f"{row['creator'].lower()}/{row['swarm_hash']}.{extension}"
    pp_extension = row['profile_picture_extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{row['creator'].lower()}.{pp_extension}"
    image = {'seller': row['seller'],
             'username': row['creator'],
             'title': row['title'],
             'extension': f"{row['extension']}",
             'uri': f"data:image/{extension};base64,{download_blob_data(container, image_path)}",
             'token_id': row['token_id'],
             'price': row['price'],
             'pp': f"data:image/{pp_extension};base64,{download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)}"}
    return image


def cancel_resale(token_id: int) -> bool:
    address = get_address_of_resale(token_id)
    tx_id = transfer_nft_to_user(token_id, address)
    tx_info = wait_for_confirmation(tx_id)
    if bool(tx_info.get('confirmed-round')):
        query = f"DELETE FROM {SCHEMA}.{RESELL_TABLE_NAME} WHERE token_id={token_id}"
        SqlManager().execute_query(query, True)
        return True
    return False


def create_new_image(username: str, file: FileStorage, title: str, price: int, end_date: datetime, is_public: int,
                     is_nsfw: int) -> None:
    extension = DICTIONARY_FORMAT[secure_filename(file.filename).split('.')[-1].lower()]
    swarm_hash_all = upload_image_swarm(file, username, is_public)
    swarm_hash = swarm_hash_all[:64]
    swarm_key = swarm_hash_all[64:]
    is_public_bool = bool(is_public)
    token_id = mint_official_nft(swarm_hash=swarm_hash,
                                 is_public=is_public_bool,
                                 username=username,
                                 title=title,
                                 number=0)
    query = f"INSERT INTO {SCHEMA}.{TOKEN_TABLE_NAME} " \
            f"(token_id, username, swarm_hash, title, extension, number, is_public, is_nsfw) " \
            f"VALUES ({token_id}, '{username}', '{swarm_hash}', '{title}', '{extension}', 1, {is_public}, {is_nsfw})"
    SqlManager().execute_query(query, True)
    query = f"INSERT INTO {SCHEMA}.{SWARM_ENCRYPT_TABLE_NAME} (token_id, swarm_hash, swarm_key) " \
            f"VALUES ({token_id}, '{swarm_hash}', '{swarm_key}')"
    SqlManager().execute_query(query, True)
    query = f"INSERT INTO {SCHEMA}.{NEW_SELL_TABLE_NAME} " \
            f"(token_id, start_price, current_price, end_date) VALUES ({token_id}, {price}, {price}, '{end_date}')"
    SqlManager().execute_query(query, True)


def create_resale(username: str, token_id: int, price: int, tx_id: str) -> None:
    tx_info = wait_for_confirmation(tx_id)
    address = tx_info.get('txn').get('txn').get('snd')
    xaid = tx_info.get('txn').get('txn').get('xaid')
    confirmed = bool(tx_info.get('confirmed-round'))
    if xaid == token_id and confirmed and token_id in list_account_assets(ADDRESS_ALGO_OURSELF):
        query = f"INSERT INTO {SCHEMA}.{RESELL_TABLE_NAME} (username, address, token_id, price) " \
                f"VALUES ('{username}', '{address}', {token_id}, {price})"
        SqlManager().execute_query(query, True)


def download_blob_data(container: str, filename: str):
    blob_client = BlobClient.from_connection_string(BLOB_CONNECTION_STRING, container, filename.lower())
    return base64.b64encode(blob_client.download_blob().readall()).decode('ascii')


def execute_bid(token_id, price, address):
    query = f"UPDATE {SCHEMA}.{NEW_SELL_TABLE_NAME} SET current_price={price}, address='{address}', " \
            f"end_date=(SELECT CASE WHEN end_date > DATEADD(minute, 10, GETUTCDATE()) " \
            f"THEN end_date ELSE DATEADD(minute, 10, GETUTCDATE()) " \
            f"END AS end_date FROM NewSell WHERE token_id={token_id}) " \
            f"WHERE token_id={token_id}"
    SqlManager().execute_query(query, True)


def execute_buy(token_id):
    query = f"DELETE FROM {SCHEMA}.{RESELL_TABLE_NAME} WHERE token_id={token_id}"
    SqlManager().execute_query(query, True)


def get_data_from_token_id(token_ids: list):
    query = f"SELECT {SCHEMA}.{TOKEN_TABLE_NAME}.username, extension, swarm_hash, title, token_id, Token.is_public, " \
            f"profile_picture_extension " \
            f"FROM {SCHEMA}.{TOKEN_TABLE_NAME} " \
            f"LEFT JOIN {SCHEMA}.{ACCOUNT_TABLE_NAME} " \
            f"ON {SCHEMA}.{TOKEN_TABLE_NAME}.username = {SCHEMA}.{ACCOUNT_TABLE_NAME}.username " \
            f"WHERE token_id in ({','.join(str(token_id) for token_id in token_ids)})"
    df = SqlManager().query_df(query)
    return df


def get_image_from_address(address: str, page: int, my: bool) -> list:
    token_ids = list_account_assets(address)
    if len(token_ids) > 0:
        df = get_data_from_token_id(token_ids)
        df = df.loc[page * NUMBER_PRINT_IMAGE:(page + 1) * NUMBER_PRINT_IMAGE - 1]
        num_cores = multiprocessing.cpu_count()
        images = Parallel(n_jobs=num_cores)(delayed(build_image_gallery)(row, my) for _, row in df.iterrows())
        return images
    return []


def get_new_images(page: int, username: str = None, email: str = None, follower: str = None, my: bool = False) -> list:
    query = f"SELECT * FROM {SCHEMA}.{NEW_SELL_VIEW_NAME}"
    if follower is not None:
        query += f" WHERE username in (SELECT star FROM [dbo].[FollowersView] WHERE follower='{follower}')"
    df = SqlManager().query_df(query)
    df.sort_values('end_date', inplace=True)
    if username is not None:
        df = df[df['username'].str.lower() == username.lower()]
    if email is not None:
        df = df[df['username'].str.lower() != get_username_from_email(email).lower()]
    df.reset_index(inplace=True)
    df = df.loc[page * NUMBER_PRINT_IMAGE:(page + 1) * NUMBER_PRINT_IMAGE - 1]
    num_cores = multiprocessing.cpu_count()
    new_images = Parallel(n_jobs=num_cores)(delayed(build_new_image)(row, my) for _, row in df.iterrows())
    return new_images


def get_resale(page: int, username: str = None, email: str = None, follower: str = None, my: bool = False) -> list:
    query = f"SELECT * FROM {SCHEMA}.{RESELL_VIEW_NAME}"
    if follower is not None:
        query += f" WHERE username in (SELECT star FROM [dbo].[FollowersView] WHERE follower='{follower}')"
    df = SqlManager().query_df(query)
    df.sort_values('price', inplace=True)
    if username is not None:
        df = df[df['seller'].str.lower() == username.lower()]
    if email is not None:
        df = df[df['seller'].str.lower() != get_username_from_email(email).lower()]
    df.reset_index(inplace=True)
    df = df.loc[page * NUMBER_PRINT_IMAGE:(page + 1) * NUMBER_PRINT_IMAGE - 1]
    num_cores = multiprocessing.cpu_count()
    resale_images = Parallel(n_jobs=num_cores)(delayed(build_resale_images)(row, my) for _, row in df.iterrows())
    return resale_images


def upload_image_swarm(file: FileStorage, username: str, is_public) -> (str, str):
    image_format = DICTIONARY_FORMAT[secure_filename(file.filename).split('.')[-1].lower()]
    url = SWARM_URL_NODE
    if is_public:
        headers = {"content-type": f"image/{image_format}"}
    else:
        headers = {"content-type": f"image/{image_format}", "Swarm-Encrypt": "true"}
    result = requests.post(url, data=file, headers=headers)
    # swarm_hash = json.loads(result.content.decode('utf8'))["reference"]
    swarm_hash = result.content.decode('utf8')
    image = Image.open(file)
    output = io.BytesIO()
    image.save(output, format=image_format)
    hex_data = output.getvalue()
    blob_client = BlobClient.from_connection_string(BLOB_CONNECTION_STRING, IMAGES_CONTAINER,
                                                    f"{username.lower()}/{swarm_hash}.{image_format}")
    blob_client.upload_blob(hex_data, overwrite=True)
    blurry_image = Image.open(file).filter(ImageFilter.BoxBlur(30))
    blurry_output = io.BytesIO()
    blurry_image.save(blurry_output, format=image_format)
    blurry_hex_data = blurry_output.getvalue()
    blurry_blob_client = BlobClient.from_connection_string(BLOB_CONNECTION_STRING, BLURRY_IMAGES_CONTAINER,
                                                           f"{username.lower()}/{swarm_hash}.{image_format}")
    blurry_blob_client.upload_blob(blurry_hex_data, overwrite=True)
    return swarm_hash
