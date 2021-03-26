from algosdk import mnemonic
from algosdk.v2client import algod
from flask import Flask
from flask_socketio import SocketIO
import os


app = Flask(__name__)
socketio = SocketIO(app, logger=False, engineio_logger=False)
dict_bid = {}
dict_buy = {}

algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "Jd6iCCXxkG6HAeKl5ewYI9LCsP1D3tS37NgRRCXn"
headers = {"X-API-Key": algod_token}
algod_client = algod.AlgodClient(algod_token=algod_token, algod_address=algod_address, headers=headers)

word_mnemonic = os.environ["mnemonic"]
accounts = {1: {'pk': mnemonic.to_public_key(word_mnemonic), 'sk': mnemonic.to_private_key(word_mnemonic)}}

CONNECTION_STRING = os.environ["database_conn"]
BLOB_CONNECTION_STRING = os.environ["blob_conn"]
APPLICATION_INSIGHT_MAIL_URL = os.environ["insight_url"]
