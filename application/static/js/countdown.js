function createCountdown(initialDate, countdown) {
    console.log(initialDate);
    var countDownDate = new Date(initialDate).getTime();
    var x = setInterval(function () {
        var now = localDateToUTC(new Date()).getTime();
        var distance = countDownDate - now;
        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        minutes = (minutes < 10) ? "0" + minutes : minutes;
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        seconds = (seconds < 10) ? "0" + seconds : seconds;

        countdown.innerText = + days + " days and " + hours + ":"
            + minutes + ":" + seconds + "";

        if (distance < 0) {
            clearInterval(x);
            countdown.innerHTML = "EXPIRED";
        }
    }, 1000);
}

function localDateToUTC(localDate) {
    return new Date(localDate.getUTCFullYear(), localDate.getUTCMonth(), localDate.getUTCDate(),
                    localDate.getUTCHours(), localDate.getUTCMinutes(), localDate.getUTCSeconds());
}