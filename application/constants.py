REGEX_FULLNAME = "^[a-zA-Z0-9 ]*$"


# ALL SQL CONSTANT
SCHEMA = "dbo"
ACCOUNT_TABLE_NAME = "Account"
FOLLOWERS_TABLE_NAME = "Followers"
FOLLOWERS_VIEW = "FollowersView"
TEMP_ACCOUNT_TABLE_NAME = "NewAccount"
ACCESS_TOKEN_BLACKLIST_TABLE = "AccessTokenBlacklist"
NEW_SELL_TABLE_NAME = "NewSell"
NEW_SELL_VIEW_NAME = "CurrentNewSellView"
RESELL_TABLE_NAME = "Resale"
RESELL_VIEW_NAME = "CurrentResaleView"
TOKEN_TABLE_NAME = "Token"

DICTIONARY_FORMAT = {
    'png': 'png',
    'jpeg': 'jpeg',
    'jpg': 'jpeg'
}

ADDRESS_ALGO_OURSELF = 'HKDGSHRLJJLQP463PPTGIRQWMSPOIWR5CGAOCKOHOEH3WEU44SEYIDHPR4'
PROFILE_PICTURES_CONTAINER = "profile"


# CONNECTION_STRING = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:starpicserver.database.windows.net,1433;Database=starpic;Uid=main_admin;Pwd=Password1;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
APPLICATION_INSIGHT_MAIL_URL = "https://prod-05.francecentral.logic.azure.com:443/workflows/99dbadb3eca946519f25e7829" \
                               "d1e0b77/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2" \
                               "Frun&sv=1.0&sig=QUnZEinH4u1wra3bJ9nPakFxOkt5DYTYaMbQ_A-jpcI"
BLOB_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=mypic;AccountKey=Po7bUVzGfC8V00KLcA02loMAOg60TN+/nB8hGQf9rQvOc2sQmKKahZ7xvBmIiAFgSqxDIGv1YUGlTha62bAejQ==;EndpointSuffix=core.windows.net"


from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

keyVaultName = 'mypic-keyvault-prd'
KVUri = f"https://{keyVaultName}.vault.azure.net"

credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)
secret = client.get_secret("database-conn")
CONNECTION_STRING = secret.value