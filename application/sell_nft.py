from algosdk import algod, mnemonic, transaction, template

from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, AssetFreezeTxn, PaymentTxn

from algosdk.v2client import algod

# Specify your node address and token. This must be updated.

# helper function that converts a mnemonic passphrase into a private signing key
def get_private_key_from_mnemonic(mn) :
    private_key = mnemonic.to_private_key(mn)
    return private_key

# helper function that converts a mnemonic passphrase into a private signing key
def get_public_key_from_mnemonic(mn) :
    public_key = mnemonic.to_public_key(mn)
    return public_key

def wait_for_confirmation(client, txid):
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
    return txinfo

def sell_nft(algod_client, micro_algo_price, assetID, expiry_round, buyer_public_key, seller_private_key):
    ratn = 1
    ratd = micro_algo_price
    expiry_round = expiry_round
    min_trade = (ratd-1)
    max_fee = 2000 # because 2 grouped transactions
    assetID = assetID
    ## Inject template data into LimitOrder template
    limit = template.LimitOrder(buyer_public_key, assetID, ratn, ratd, expiry_round, min_trade, max_fee)
    # Get the address for the escrow account associated with the logic
    escrow_addr = limit.get_address()
    # Retrieve the program bytes
    program = limit.get_program()
    # Create the grouped transactions against the Limt contract
    asset_amount = 1 # 1 NFT = amount of 1
    micro_algo_amount = micro_algo_price
    # Get suggested parameters from the network
    tx_params = algod_client.suggested_params()

    # set fee to 0 to get minimum fee
    fee = 0
    # contract, amount: int, fee: int, first_valid, last_valid, gh
    txns = limit.get_swap_assets_transactions(program, asset_amount,
                                            micro_algo_amount, seller_private_key,
                                            tx_params.first,
                                            tx_params.first + 1000,
                                            tx_params.gh, fee)
    return escrow_addr, txns

def opt_in_asset(algod_client, asset_id, public_key, private_key):
    params = algod_client.suggested_params()
    # comment these two lines if you want to use suggested params
    params.fee = 1000
    params.flat_fee = True
     # Use the AssetTransferTxn class to transfer assets and opt-in
    txn = AssetTransferTxn(
        sender=public_key,
        sp=params,
        receiver=public_key,
        amt=0,
        index=asset_id)
    stxn = txn.sign(private_key)
    txid = algod_client.send_transaction(stxn)
    # Wait for the transaction to be confirmed
    wait_for_confirmation(algod_client, txid)
    # Now check the asset holding for that account.
    # This should now show a holding with a balance of 0.
    #print_asset_holding(algod_client, public_key, asset_id)
    print("Asset ",asset_id," opted in for ACCOUNT ",public_key,"\n")


#   Utility function to list assets from an account (will filter assets that have a quantity =/= 1)
def list_all_account_assets(algod_client, account):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then loop thru the accounts returned and match the account you are looking for
    account_info = algod_client.account_info(account)
    asset_list = []
    for idx, my_account_info in enumerate(account_info['assets']):
        scrutinized_asset = account_info['assets'][idx]
        asset_list.append(scrutinized_asset['asset-id'])
    return asset_list

def transfer_nft_to_user(algod_client, asset_id, mypic_public_key, mypic_private_key, user_public_key):
    params = algod_client.suggested_params()
    # comment these two lines if you want to use suggested params
    params.fee = 1000
    params.flat_fee = True
    txn = AssetTransferTxn(
        sender=mypic_public_key,
        sp=params,
        receiver=user_public_key,
        amt=1,
        index=asset_id)
    stxn = txn.sign(mypic_private_key)
    txid = algod_client.send_transaction(stxn)
    return txid

def transfer_algo_to_user(algod_client, sender, receiver, micro_algo_amount, mypic_public_key, user_public_key, mypic_private_key):
    params = algod_client.suggested_params()
    txn = PaymentTxn(sender, params, receiver, micro_algo_amount)
    stxn = txn.sign(mypic_private_key)
    txid = algod_client.send_transaction(stxn)
    return txid

def send_transactions(algod_client, txs):
    txid = algod_client.send_transactions(txs)
    return txid


algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "Jd6iCCXxkG6HAeKl5ewYI9LCsP1D3tS37NgRRCXn"
headers = {
   "X-API-Key": algod_token,
}

# Initialize an algod client
algod_client_ = algod.AlgodClient(algod_token=algod_token, algod_address=algod_address, headers=headers)
buyer_mnemonic = "palm bike stove away tent loud aisle love man help faculty vendor crouch yellow interest orphan next gift poem accuse gift lawsuit field above abstract"
buyer_private_key = get_private_key_from_mnemonic(buyer_mnemonic)
buyer_public_key = get_public_key_from_mnemonic(buyer_mnemonic)
opt_in_asset(algod_client_, 15037227, buyer_public_key, buyer_private_key)
status = algod_client_.status()


# seller_mnemonic = "behave vicious issue asthma welcome zone matrix matter round mechanic future estate label team name draft brain shop subway orbit jewel coin brain able hen"
# buyer_mnemonic = "tattoo market oven bench betray double tuna box sand lottery champion spend melt virus motor label bacon wine rescue custom cannon pen merry absorb endorse"
#
# #asset_owner_sk = mnemonic.to_private_key(asset_owner_mn)
#
# seller_private_key = get_private_key_from_mnemonic(seller_mnemonic)
# seller_public_key = get_public_key_from_mnemonic(seller_mnemonic)
#
# buyer_private_key = get_private_key_from_mnemonic(buyer_mnemonic)
# buyer_public_key = get_public_key_from_mnemonic(buyer_mnemonic)
#
# print("Seller address = ",seller_public_key)
# print("Buyer address = ",buyer_public_key)
#
# last_round = status['last-round']
# #example 14675037
#
# assetID_to_swap = 14674941 #can try 14675037 and 14675238
#
# price_ = 250000
# ################################################################################################################
# smartcontract_addr, swap_txns = sell_nft(   algod_client = algod_client_,
#                                             micro_algo_price = price_,
#                                             assetID = assetID_to_swap,
#                                             expiry_round  = 13114964+1000, #last_round + 1000,
#                                             seller_private_key = seller_private_key,
#                                             buyer_public_key = buyer_public_key
#                                             )
#
# print("smart contract addr, for the BUYER to fund with ALGO = ",smartcontract_addr)
#
# print("funding contract with 0.12 algo...")
# params = algod_client_.suggested_params()
# params.fee = 1000
# amount = 120000
# txn = PaymentTxn(seller_public_key, params, smartcontract_addr, amount)
# stxn = txn.sign(seller_private_key)
# txid = algod_client_.send_transaction(stxn)
# print("funding contract Tx = ",txid)
#
#
# print("\nAutomatic opt in for test:")
# buyer_assets = list_all_account_assets(algod_client_, buyer_public_key)
# if assetID_to_swap in buyer_assets:
#     print("Already opt-ed in.")
# else:
#     opt_in_asset(algod_client_, assetID_to_swap, buyer_public_key, buyer_private_key)
#     input("Press Enter after BUYER has opted-in for the asset...")
#
#
# params = algod_client_.suggested_params()
# params.fee = 1000
# amount = price_
# txn = PaymentTxn(buyer_public_key, params, smartcontract_addr, amount)
# stxn = txn.sign(buyer_private_key)
# txid = algod_client_.send_transaction(stxn)
# print("Simulating Buyer Tx = ",txid)
#
# input("Press Enter to continue AFTER BUYER DEPOSITED RIGHT AMOUNT & SMART CONTRACT FUNDED ...")
#
#
# input("Press Enter to send grouped txs....")
#
# txid = send_transactions(algod_client_,swap_txns)
# print("SWAP Double Transaction ID: {}".format(txid))
