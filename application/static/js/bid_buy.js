function bid(token_id, price, url) {
    let bidPrice = price.value;
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            console.log(http.responseText)
            let parsed = JSON.parse(http.responseText);
            if (parsed.status == 404) {
                console.log("Could not bid", parsed.e);
                alert("Could not process the bid: ", parsed.e);
            } else if (parsed.status == 200) {
                AlgoPay(parsed.to, parsed.amount, parsed.note, token_id, url, "validate_new");
            }
        }
    }
    http.send("token_id=" + token_id + "&type=new" + "&price=" + bidPrice);
}

function buy(token_id, price, url) {
    console.log(price);
    let bidPrice = parseInt(price.innerText);
    AlgoSignIn(bidPrice, token_id, url);
}

function sell(token_id, price, url) {
    AlgoTransferAsset(token_id, price, url);
}

function cancel(token_id, url) {
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            console.log(http.responseText);
        }
    }
    http.send("token_id=" + token_id + "&type=cancel");
}