from application import dict_buy
from application.market import execute_buy
from application.smart_contract import (
    create_resale_smart_contract,
    fund_smart_contract,
    send_transactions,
    verify_buy_transaction,
    wait_for_confirmation
)
import json


def manage_buy(form, username):
    error = None
    if 'token_id' not in form:
        error = 'Token ID is required.'
    try:
        int(form['token_id'])
    except ValueError:
        error = "Enter an integer for token ID."
    if 'price' not in form:
        error = 'Price is required.'
    try:
        int(form['price'])
    except ValueError:
        error = "Enter an integer for price"
    if 'address' not in form:
        error = 'Transaction ID is required.'

    if error is None:
        token_id = int(form['token_id'])
        price = int(form['price'])
        address = form['address']
        if form['type'] == 'resale':
            micro_price = price * 1000000
            smartcontract_address, swap_tx = create_resale_smart_contract(micro_price, token_id, address)
            tx_id = fund_smart_contract(smartcontract_address)
            tx_info = wait_for_confirmation(tx_id)
            if bool(tx_info.get('confirmed-round')):
                note = f"{username}_{token_id}_resale"
                dict_buy[note] = swap_tx
                return json.dumps({'status': 200, 'to': smartcontract_address, 'amount': micro_price, 'note': note})

        if form['type'] == 'validate_resale':
            if 'txID' not in form:
                error = 'Transaction ID is required.'
            if error is None:
                address = form['address']
                tx_id = form['txID']
                price = int(price/1000000)
                note = f"{username}_{token_id}_resale"
                if verify_buy_transaction(tx_id):
                    tx_swap_id = send_transactions(dict_buy[note])
                    tx_swap_info = wait_for_confirmation(tx_swap_id)
                    if bool(tx_swap_info.get('confirmed-round')):
                        execute_buy(token_id)
                        dict_buy.pop(note, None)
                        return "Buy done"
    return error
