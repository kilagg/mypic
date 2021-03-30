from application import BLOB_CONNECTION_STRING, LOGIC_APP_MAIL_URL
from application.constants import *
from application.sql_manager import SqlManager
from azure.storage.blob import BlobClient
from hashlib import sha256
from typing import Optional
from werkzeug.datastructures import FileStorage
import random
import requests


def check_code(code: int, email: str) -> bool:
    if email_in_tmp_db(email):
        query = f"SELECT code FROM {SCHEMA}.{TEMP_ACCOUNT_TABLE_NAME} WHERE email='{email}'"
        return SqlManager().query_df(query).loc[0, 'code'] == code
    return False


def email_in_tmp_db(email: str) -> bool:
    query = f"SELECT COUNT(*) AS total FROM {SCHEMA}.{TEMP_ACCOUNT_TABLE_NAME} WHERE email='{email}'"
    return SqlManager().query_df(query).loc[0, 'total'] == 1


def email_in_db(email: str) -> bool:
    query = f"SELECT COUNT(*) AS total FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE email='{email}'"
    return SqlManager().query_df(query).loc[0, 'total'] == 1


def follow(follower: str, star: str) -> None:
    if username_in_db(follower) and username_in_db(star) and not is_follow(follower, star):
        query = f"INSERT INTO {SCHEMA}.{FOLLOWERS_TABLE_NAME} " \
                f"VALUES ((SELECT id FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE username='{follower}'), " \
                f"(SELECT id FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE username='{star}'))"
        SqlManager().execute_query(query, True)


def is_follow(follower: str, star: str) -> bool:
    query = f"SELECT COUNT(*) AS total FROM {SCHEMA}.{FOLLOWERS_VIEW} WHERE follower='{follower}' AND star='{star}'"
    return SqlManager().query_df(query).loc[0, 'total'] == 1


def get_address_from_email(email: str) -> Optional[str]:
    if email_in_db(email):
        query = f"SELECT address FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE email='{email}'"
        return SqlManager().query_df(query).loc[0, 'address']
    return None


def get_address_from_username(username: str) -> Optional[str]:
    if username_in_db(username):
        query = f"SELECT address FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE username='{username}'"
        return SqlManager().query_df(query).loc[0, 'address']
    return None


def get_address_of_resale(token_id: int) -> Optional[str]:
    if token_id_in_resale(token_id):
        query = f"SELECT address FROM {SCHEMA}.{RESELL_TABLE_NAME} WHERE token_id='{token_id}'"
        return SqlManager().query_df(query).loc[0, 'address']
    return None


def get_current_price_from_token_id(token_id: int) -> Optional[int]:
    if token_id_in_new_sell(token_id):
        query = f"SELECT current_price FROM {SCHEMA}.{NEW_SELL_TABLE_NAME} WHERE token_id={token_id}"
        return SqlManager().query_df(query).loc[0, 'current_price']
    return None


def get_nsfw_from_email(email: str) -> Optional[bool]:
    if email_in_db(email):
        query = f"SELECT nsfw FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE email='{email}'"
        return bool(SqlManager().query_df(query).loc[0, 'nsfw'])
    return None


def get_username_of_resale(token_id: int) -> Optional[str]:
    if token_id_in_resale(token_id):
        query = f"SELECT username FROM {SCHEMA}.{RESELL_TABLE_NAME} WHERE token_id='{token_id}'"
        return SqlManager().query_df(query).loc[0, 'username']
    return None


def get_followers_from_username(username: str) -> Optional[int]:
    if username_in_db(username):
        query = f"SELECT count(*) as total_followers " \
                f"FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} RIGHT JOIN {SCHEMA}.{FOLLOWERS_TABLE_NAME} " \
                f"ON {SCHEMA}.{ACCOUNT_TABLE_NAME}.[id]={SCHEMA}.{FOLLOWERS_TABLE_NAME}.star_id" \
                f"  WHERE username='{username}'"
        return SqlManager().query_df(query).loc[0, 'total_followers']
    return None


def get_fullname_from_email(email: str) -> Optional[str]:
    if email_in_db(email):
        query = f"SELECT fullname FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE email='{email}'"
        return SqlManager().query_df(query).loc[0, 'fullname']
    return None


def get_fullname_from_username(username: str) -> Optional[str]:
    if username_in_db(username):
        query = f"SELECT fullname FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE username='{username}'"
        return SqlManager().query_df(query).loc[0, 'fullname']
    return None


def get_is_public_from_username(username: str) -> Optional[bool]:
    if username_in_db(username):
        query = f"SELECT is_public FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE username='{username}'"
        return SqlManager().query_df(query).loc[0, 'is_public']
    return None


def get_password_from_email(email: str) -> Optional[str]:
    if email_in_db(email):
        query = f"SELECT password FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE email='{email}'"
        return SqlManager().query_df(query).loc[0, 'password']
    return None


def get_previous_bidder(token_id: int):
    if token_id_in_new_sell(token_id):
        query = f"SELECT address FROM {SCHEMA}.{NEW_SELL_TABLE_NAME} WHERE token_id='{token_id}'"
        return SqlManager().query_df(query).loc[0, 'address']
    return None


def get_profile_picture_extension_from_email(email: str) -> Optional[str]:
    if email_in_db(email):
        query = f"SELECT profile_picture_extension FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE email='{email}'"
        return SqlManager().query_df(query).loc[0, 'profile_picture_extension']
    return None


def get_profile_picture_extension_from_username(username: str) -> Optional[str]:
    if username_in_db(username):
        query = f"SELECT profile_picture_extension FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE username='{username}'"
        return SqlManager().query_df(query).loc[0, 'profile_picture_extension']
    return None


def get_stars_from_follower(follower: str):
    query = f"SELECT star FROM [dbo].[FollowersView] WHERE follower='{follower}' ORDER BY star"
    return list(SqlManager().query_df(query)['star'])


def get_username_from_email(email: str) -> Optional[str]:
    if email_in_db(email):
        query = f"SELECT username FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE email='{email}'"
        return SqlManager().query_df(query).loc[0, 'username']
    return None


def insert_jti_in_blacklist(jti: str) -> None:
    query = f"INSERT INTO {SCHEMA}.{ACCESS_TOKEN_BLACKLIST_TABLE} (jti) VALUES ('{jti}')"
    SqlManager().execute_query(query, True)


def jti_in_blacklist(jti: str) -> bool:
    query = f"SELECT COUNT(*) AS total FROM {SCHEMA}.{ACCESS_TOKEN_BLACKLIST_TABLE} WHERE jti='{jti}'"
    return SqlManager().query_df(query).loc[0, 'total'] == 1


def hash_password(password: str) -> str:
    return sha256(password.encode('utf-8')).hexdigest()


def save_to_db(email: str) -> None:
    query = f"INSERT INTO {SCHEMA}.{ACCOUNT_TABLE_NAME} (email, username, password, fullname) " \
            f"SELECT email, username, password, fullname FROM {SCHEMA}.{TEMP_ACCOUNT_TABLE_NAME} " \
            f"WHERE email='{email}'"
    SqlManager().execute_query(query, True)


def save_to_db_temp(reason: str, email: str, username: str = None, password: str = None, fullname: str = None) -> None:
    code = random.randint(100000, 999999)
    query = f"DELETE FROM {SCHEMA}.{TEMP_ACCOUNT_TABLE_NAME}  WHERE email='{email}'"
    SqlManager().execute_query(query, True)
    query = f"INSERT INTO {SCHEMA}.{TEMP_ACCOUNT_TABLE_NAME} (email, username, password, fullname, code) " \
            f"VALUES ('{email}', '{username}', '{password}', '{fullname}', {code})"
    SqlManager().execute_query(query, True)
    # TODO : remove print
    print(code)
    data = {"body": f"Your validation code : {code}",
            "email": f"{email}",
            "object": f"MyPic Security - {reason}"}
    headers = {"Content-Type": "application/json"}
    requests.post(LOGIC_APP_MAIL_URL, headers=headers, json=data)


def token_id_in_new_sell(token_id: int) -> bool:
    query = f"SELECT COUNT(*) AS total FROM {SCHEMA}.{NEW_SELL_TABLE_NAME} WHERE token_id={token_id}"
    return SqlManager().query_df(query).loc[0, 'total'] == 1


def token_id_in_resale(token_id: int) -> bool:
    query = f"SELECT COUNT(*) AS total FROM {SCHEMA}.{RESELL_TABLE_NAME} WHERE token_id={token_id}"
    return SqlManager().query_df(query).loc[0, 'total'] == 1


def unfollow(follower: str, star: str) -> None:
    if username_in_db(follower) and username_in_db(star):
        query = f"DELETE FROM {SCHEMA}.{FOLLOWERS_TABLE_NAME} " \
                f"WHERE follower_id=(SELECT id FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE username='{follower}') " \
                f"AND star_id=(SELECT id FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE username='{star}')"
        SqlManager().execute_query(query, True)


def update_address(email: str, address: str) -> None:
    query = f"UPDATE {SCHEMA}.{ACCOUNT_TABLE_NAME} SET address='{address}' WHERE email='{email}'"
    SqlManager().execute_query(query, True)


def update_fullname(email: str, fullname: str) -> None:
    query = f"UPDATE {SCHEMA}.{ACCOUNT_TABLE_NAME} SET fullname='{fullname}' WHERE email='{email}'"
    SqlManager().execute_query(query, True)


def update_is_public(email: str, is_public: int) -> None:
    query = f"UPDATE {SCHEMA}.{ACCOUNT_TABLE_NAME} SET is_public={is_public} WHERE email='{email}'"
    SqlManager().execute_query(query, True)


def update_nsfw(email: str, nsfw: int) -> None:
    query = f"UPDATE {SCHEMA}.{ACCOUNT_TABLE_NAME} SET nsfw={nsfw} WHERE email='{email}'"
    SqlManager().execute_query(query, True)


def update_profile_picture(username: str, data: FileStorage, extension: str) -> None:
    blob_client = BlobClient.from_connection_string(BLOB_CONNECTION_STRING, PROFILE_PICTURES_CONTAINER,
                                                    f"{username.lower()}.{extension}")
    blob_client.upload_blob(data)
    query = f"UPDATE {SCHEMA}.{ACCOUNT_TABLE_NAME} SET profile_picture_extension='{extension}' " \
            f"WHERE username='{username}'"
    SqlManager().execute_query(query, True)


def update_password(email: str, password: str) -> None:
    query = f"UPDATE {SCHEMA}.{ACCOUNT_TABLE_NAME} SET password='{password}' WHERE email='{email}'"
    SqlManager().execute_query(query, True)


def username_in_db(username: str) -> bool:
    query = f"SELECT COUNT(*) AS total FROM {SCHEMA}.{ACCOUNT_TABLE_NAME} WHERE username='{username}'"
    return SqlManager().query_df(query).loc[0, 'total'] == 1
