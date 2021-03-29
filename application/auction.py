from application import dict_bid, socketio
from application.constants import *
from application.market import execute_bid
from application.user import get_current_price_from_token_id, get_previous_bidder
from datetime import datetime, timedelta
from flask import redirect, url_for
from application.smart_contract import transfer_algo_to_user, verify_bid_transaction, verify_buy_transaction
import json


def manage_auction(form, username):
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

    if error is None:
        token_id = int(form['token_id'])
        price = int(form['price'])
        if form['type'] == 'new':
            if price < int(get_current_price_from_token_id(token_id) * 1.1) + 1:
                return json.dumps({"status": 404, 'e': 'Price is not enough'})
            if token_id in dict_bid and dict_bid[token_id][0] + timedelta(minutes=3) > datetime.utcnow():
                return json.dumps({"status": 404, 'e': 'Someone process a bid, retry in few seconds'})
            dict_bid[token_id] = [datetime.utcnow(), username, price]
            return json.dumps({'status': 200,
                               'to': ADDRESS_ALGO_OURSELF,
                               'amount': price * 1000000,
                               'note': f"{username}_{token_id}"})

        if form['type'] == 'error_new':
            dict_bid.pop(token_id, None)
            return "Delete from queue"

        if form['type'] == 'validate_new':
            if 'address' not in form:
                error = 'Address is required.'
            if 'txID' not in form:
                error = 'Transaction ID is required.'
            if error is None:
                address = form['address']
                tx_id = form['txID']
                price = int(price/1000000)
                if verify_bid_transaction(tx_id, price, username, token_id, address):
                    if username == dict_bid[token_id][1] and price == dict_bid[token_id][2]:
                        old_price = int(get_current_price_from_token_id(token_id))
                        old_address = get_previous_bidder(token_id)
                        execute_bid(token_id, price, address)
                        dict_bid.pop(token_id, None)
                        socketio.emit("new", data=[str(int(price * 1.1) + 1), token_id])
                        if old_address is not None:
                            tx_id = transfer_algo_to_user(old_address, old_price * 1000000)
                            if verify_buy_transaction(tx_id):
                                return "Bid was done."
                    else:
                        tx_id = transfer_algo_to_user(address, price * 1000000)
                        if verify_buy_transaction(tx_id):
                            return "Refund"
                else:
                    return "Transaction does not exist"
            return error
        return redirect(url_for('main.feed'))
    return error
