const LEDGER = 'TestNet';

function connect(callback = () => {}) {
    if (typeof AlgoSigner === 'undefined') {
        alert('AlgoSigner is not installed. Please install it.');
        return
    }

    AlgoSigner.connect()
        .then((e) => {
            AlgoSigner.accounts({
                ledger: 'TestNet'
            }).then((d) => {
                callback();
            })
            .catch((e) => {
            });
        })
        .catch((e) => {
        });
}

function account(callback = (name) => { }, errorCallback = () => { }) {
    AlgoSigner.accounts({
        ledger: 'TestNet'
    })
    .then((d) => {
        callback(d[0]['address']);
    })
    .catch((e) => {
        connect(() => {
            account(callback);
        })
        console.error(e);
    });
}

function get_param(callback = (txParams) => { }, errorCallback = () => { }) {
    AlgoSigner.algod({
        ledger: LEDGER,
        path: '/v2/transactions/params'
    })
    .then((d) => {
        callback(d);
    })
    .catch((e) => {
        errorCallback();
        console.error(e);
    });
}


function pay(from, to, amount, note, txParams, callback = (status) => { }, errorCallback = () => { }) {
    AlgoSigner.sign({
        from: from,
        to: to,
        amount: amount,
        note: note,
        type: 'pay',
        fee: txParams['fee'],
        firstRound: txParams['last-round'],
        lastRound: txParams['last-round'] + 1000,
        genesisID: txParams['genesis-id'],
        genesisHash: txParams['genesis-hash']
    })
    .then((d) => {
        callback(d);
    })
    .catch((e) => {
        errorCallback();
        console.error(e);
    });
}

function get_status(txID) {
    AlgoSigner.algod({
        ledger: 'TestNet',
        path: '/v2/transactions/pending/' + txID
    })
        .then((d) => {
            console.log(d);
        })
        .catch((e) => {
            console.error(e);
        });
}

function send_algo(signedTx, callback = (status) => { }, errorCallback = () => {}) {
    AlgoSigner.send({
        ledger: 'TestNet',
        tx: signedTx.blob
    })
    .then((d) => {
        callback(d);
    })
    .catch((e) => {
        console.error(e);
        errorCallback();
    });
}

function AlgoPay(to, amount, note, token_id, url, type) {
    account((from) => {
        get_param((tx) => {
            pay(from, to, amount, note, tx, (signedTx) => {
                send_algo(signedTx, (s) => {
                    console.log(s);
                    get_status(signedTx.txID);
                    submitTransaction(amount, from, token_id, url, signedTx.txID, type);
                }, () => {
                    cancelTransaction(amount, from, token_id, url);
                });
            }, () => {
                cancelTransaction(amount, from, token_id, url);
            });
        }, () => {
            cancelTransaction(amount, from, token_id, url);
        });
    });
}

function submitTransaction(amount, from, token_id, url, txID, type) {
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            console.log(http.responseText)
        }
    }
    http.send("token_id=" + token_id + "&type=" + type + "&price=" + amount + "&address=" + from + "&txID=" + txID);
}


function cancelTransaction(amount, from, token_id, url) {
    console.log(url)
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            console.log(http.responseText)
        }
    }
    http.send("token_id=" + token_id + "&type=error_new" + "&price=" + amount + "&address=" + from);
}

function setupTX(from, txParams, token_id, callback=() => {}) {
    let txn = {
        type: 'axfer',
        from: from,
        to: 
        "HKDGSHRLJJLQP463PPTGIRQWMSPOIWR5CGAOCKOHOEH3WEU44SEYIDHPR4",
        fee: txParams['fee'],
        firstRound: txParams['last-round'],
        lastRound: txParams['last-round'] + 1000,
        genesisID: txParams['genesis-id'],
        genesisHash: txParams['genesis-hash'],

        amount: 1,
        assetIndex: token_id
    };
    callback(txn)
}


function AlgoTransferAsset(token_id, price, url) {
    account((from) => {
        get_param((txParams) => {
            setupTX(from, txParams, token_id, (txn) => {
                AlgoSigner.sign(txn)
                    .then((d) => {
                        signedTx = d;
                        send_algo(d, (s) => {
                            validateTransfer(token_id, price, url, signedTx.txID);
                        });
                    })
                    .catch((e) => {
                        console.error(e);
                    });
            });
        });
    });
}

function validateTransfer(token_id, price, url, txID) {
    let bidPrice = price.value;
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            console.log(http.responseText);

        }
    }
    http.send("token_id=" + token_id + "&type=sell" + "&price=" + bidPrice + "&txID="+txID);
}


/// Buy

function signIn(from, token_id, note, txParams, callback = () => {}) {
    AlgoSigner.sign({
        from: from,
        to: from,
        assetIndex: token_id,
        note: note,
        amount: 0,
        type: 'axfer',
        fee: txParams['fee'],
        firstRound: txParams['last-round'],
        lastRound: txParams['last-round'] + 1000,
        genesisID: txParams['genesis-id'],
        genesisHash: txParams['genesis-hash']
    })
        .then((d) => {
            signedTx = d;
            callback(d);
        })
        .catch((e) => {
            console.error(e);
        });
}

function AlgoSignIn(amount, token_id, url) {
    let note = "";
    account((from) => {
        get_param((tx) => {
            signIn(from, token_id, note, tx, (signedTx) => {
                send_algo(signedTx, (s) => {
                    submitSignIn(amount, from, token_id, url);
                });
            });
        });
    });
}

function submitSignIn(amount, from, token_id, url) {
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            console.log(http.responseText)
            let parsed = JSON.parse(http.responseText);
            if (parsed.status == 404) {
                console.log("Could not buy", parsed.e);
                alert("Could not process the buy: ", parsed.e);
            } else if (parsed.status == 200) {
                AlgoPay(parsed.to, parsed.amount, parsed.note, token_id, url, "validate_resale");
            }
        }
    }
    http.send("token_id=" + token_id  + "&price=" + amount + "&address=" + from + "&type=resale");
}