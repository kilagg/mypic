from algosdk import mnemonic
from algosdk.v2client import algod
from flask import Flask
from flask_socketio import SocketIO
import logging


app = Flask(__name__)
logs = app.logger
logs.setLevel(logging.DEBUG)
# TODO : remove logger
socketio = SocketIO(app, logger=False, engineio_logger=False)
dict_bid = {}
dict_buy = {}

algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "Jd6iCCXxkG6HAeKl5ewYI9LCsP1D3tS37NgRRCXn"
headers = {"X-API-Key": algod_token}
algod_client = algod.AlgodClient(algod_token=algod_token, algod_address=algod_address, headers=headers)

# TODO : add word_mnemonic in key vault
word_mnemonic = "behave vicious issue asthma welcome zone matrix matter round mechanic future estate label team name draft brain shop subway orbit jewel coin brain able hen"
accounts = {1: {'pk': mnemonic.to_public_key(word_mnemonic), 'sk': mnemonic.to_private_key(word_mnemonic)}}
