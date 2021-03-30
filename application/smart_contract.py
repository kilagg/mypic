from algosdk import mnemonic, template
from algosdk.error import AlgodHTTPError
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, PaymentTxn
from application import accounts, algod_client, WORD_MNEMONIC
from application.constants import *
from binascii import unhexlify
import base64
import json


def create_resale_smart_contract(micro_price, token_id, buyer_address):
    seller_private_key = get_private_key_from_mnemonic(WORD_MNEMONIC)
    expiry_round = algod_client.status()['last-round'] + 1000
    ratn = 1
    min_trade = (micro_price - 1)
    max_fee = 2000
    limit = template.LimitOrder(buyer_address, token_id, ratn, micro_price, expiry_round, min_trade, max_fee)
    escrow_address = limit.get_address()
    program = limit.get_program()
    asset_amount = 1
    tx_params = algod_client.suggested_params()
    fee = 0
    tx_ns = limit.get_swap_assets_transactions(program, asset_amount, micro_price, seller_private_key, tx_params.first,
                                               tx_params.first + 1000, tx_params.gh, fee)
    return escrow_address, tx_ns


def fund_smart_contract(smartcontract_address):
    seller_private_key = get_private_key_from_mnemonic(WORD_MNEMONIC)
    params = algod_client.suggested_params()
    params.fee = 1000
    txn = PaymentTxn(ADDRESS_ALGO_OURSELF, params, smartcontract_address, 120000)
    stxn = txn.sign(seller_private_key)
    tx_id = algod_client.send_transaction(stxn)
    return tx_id


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


def list_account_assets(account: str) -> list:
    if account is None:
        return []
    account_info = algod_client.account_info(account)
    asset_list = [account_info['assets'][idx]['asset-id'] for idx, my_account_info in enumerate(account_info['assets'])
                  if account_info['assets'][idx]['amount'] == 1]
    return asset_list


def mint_official_nft(swarm_hash: str, is_public: bool, username: str, title: str, number: int,
                      asset_symbol: str = 'MYPIC', asset_name: str = 'MyPic NFT', website_url: str = 'http://mypic.io'):
    params = algod_client.suggested_params()
    params.fee = 1000
    params.flat_fee = True

    data_set = {"is_public": f'{is_public}', 'username': username, 'title': title, 'number': f'{number}'}

    tx_note_json_str = json.dumps(data_set)
    tx_note_bytes = tx_note_json_str.encode("utf-8")
    swarm_hash_bytes = unhexlify(swarm_hash)
    txn = AssetConfigTxn(sender=accounts[1]['pk'],
                         sp=params,
                         total=1,
                         decimals=0,
                         unit_name=asset_symbol,
                         asset_name=asset_name,
                         strict_empty_address_check=False,
                         default_frozen=False,
                         metadata_hash=swarm_hash_bytes,
                         note=tx_note_bytes,
                         manager=accounts[1]['pk'],
                         reserve=accounts[1]['pk'],
                         freeze="",
                         clawback=accounts[1]['pk'],
                         url=website_url)

    stxn = txn.sign(accounts[1]['sk'])
    tx_id = algod_client.send_transaction(stxn)
    wait_for_confirmation(tx_id)
    ptx = algod_client.pending_transaction_info(tx_id)
    asset_id = ptx["asset-index"]
    return asset_id


def send_transactions(tx):
    tx_id = algod_client.send_transactions(tx)
    return tx_id


def transfer_algo_to_user(receiver, micro_algo_amount):
    mypic_private_key = get_private_key_from_mnemonic(WORD_MNEMONIC)
    params = algod_client.suggested_params()
    txn = PaymentTxn(ADDRESS_ALGO_OURSELF, params, receiver, micro_algo_amount)
    stxn = txn.sign(mypic_private_key)
    tx_id = algod_client.send_transaction(stxn)
    return tx_id


def transfer_nft_to_user(asset_id, address):
    mypic_private_key = get_private_key_from_mnemonic(WORD_MNEMONIC)
    params = algod_client.suggested_params()
    params.fee = 1000
    params.flat_fee = True
    txn = AssetTransferTxn(
        sender=ADDRESS_ALGO_OURSELF,
        sp=params,
        receiver=address,
        amt=1,
        index=asset_id)
    stxn = txn.sign(mypic_private_key)
    tx_id = algod_client.send_transaction(stxn)
    return tx_id


def verify_bid_transaction(tx_id, price, username, token_id, address):
    try:
        tx_info = wait_for_confirmation(tx_id)
        tx_price = int(tx_info.get('txn').get('txn').get('amt') / 1000000)
        tx_note = base64.b64decode(tx_info.get('txn').get('txn').get('note')).decode('ascii')
        tx_sender = tx_info.get('txn').get('txn').get('snd')
        tx_receiver = tx_info.get('txn').get('txn').get('rcv')
        return (price == tx_price
                and f"{username}_{token_id}" == tx_note
                and tx_sender == address
                and tx_receiver == ADDRESS_ALGO_OURSELF
                and bool(tx_info.get('confirmed-round')))
    except AlgodHTTPError:
        return False


def verify_buy_transaction(tx_id):
    tx_info = wait_for_confirmation(tx_id)
    return bool(tx_info.get('confirmed-round'))


def wait_for_confirmation(tx_id):
    last_round = algod_client.status().get('last-round')
    tx_info = algod_client.pending_transaction_info(tx_id)
    while not (tx_info.get('confirmed-round') and tx_info.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        algod_client.status_after_block(last_round)
        tx_info = algod_client.pending_transaction_info(tx_id)
    print("Transaction {} confirmed in round {}.".format(tx_id, tx_info.get('confirmed-round')))
    return tx_info
