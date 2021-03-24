function objectToParam(object) {
    // Turn the data object into an array of URL-encoded key/value pairs.
    let urlEncodedData = "", urlEncodedDataPairs = [];
    console.log(Object.keys(object))
    for (let i = 0; i < Object.keys(object).length; i++) {
        urlEncodedDataPairs.push(encodeURIComponent(Object.keys(object)[i]) + '=' + encodeURIComponent(object[Object.keys(object)[i]]));
    }
    urlEncodedData = urlEncodedDataPairs[0];
    for (let i = 1; i < urlEncodedDataPairs.length; i++) {
        urlEncodedData += "&";
        urlEncodedData += urlEncodedDataPairs[i];
    }

    return urlEncodedData;
}

function postServer(url, args, callback = function () { }) {
    var http = new XMLHttpRequest();
    http.open('POST', url, true, "pqeokfe");
    http.setRequestHeader('Authorization', 'Bearer ');

    //Send the proper header information along with the request
    http.setRequestHeader('Content-type', 'application/json');

    http.withCredentials = true;

    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            callback(JSON.parse(http.responseText));
        }
    }
    http.send(JSON.stringify(args));
}

function getServer(url, access_token, callback = () => {}) {
    var http = new XMLHttpRequest();
    http.open('GET', url, true);

    //Send the proper header information along with the request
    http.setRequestHeader('Authorization', 'Bearer ' + access_token);
    http.setRequestHeader('Content-type', 'application/json');
    

    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            callback(http.responseText);
        }
    }
    http.send(null);
}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function hexToBase64(str) {
    return btoa(String.fromCharCode.apply(null, str.replace(/\r|\n/g, "").replace(/([\da-fA-F]{2}) ?/g, "0x$1 ").replace(/ +$/, "").split(" ")));
}