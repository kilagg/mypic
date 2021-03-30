let displayedFirst = { };
let endPage = { };
let requestedMorePictures = {};
let MainPage;
let Subpage;
let Errors
let SubpageType;
let currentPage;

function initGallery(mainPage, subpage, errors, subpageType) {
    MainPage = mainPage;
    Subpage = subpage;
    Errors = errors;
    SubpageType = subpageType;

    for (let page of subpage) {
        displayedFirst[page] = false;
        endPage[page] = false;
        requestedMorePictures[page] = false;
        document.getElementById(page + "_button").addEventListener("click", () => {
            switch_page(page);
        });
    }
    switch_page(subpage[0]);

    $(window).scroll((event) => {
        if (window.scrollY + window.innerHeight > 0.8 * document.documentElement.scrollHeight
            && displayedFirst[currentPage]
            && !requestedMorePictures[currentPage]
            && !endPage[currentPage]) {
            requestMore(currentPage);
        }
    });
}

function switch_page(page) {
    window.scrollTo(0, 0);
    currentPage = page;

    if (!displayedFirst[page]) {
        requestMore(page);
    }

    for (let x of Subpage) {
        if (x == page) {
            document.getElementById(x + "_div")
                .classList.remove("hidden");
            document.getElementById(x + "_button")
                .classList.add("selected");
        } else {
            document.getElementById(x + "_div")
                .classList.add("hidden");
            document.getElementById(x + "_button")
                .classList.remove("selected");
        }
    }
}

function displayImage(page, image, type) {    
    let picture_div = document.createElement("div");
    picture_div.id = "picture-" + image.token_id;
    picture_div.classList.add("picture");
    document.getElementById(page + "_div").appendChild(picture_div);

    let user = document.createElement("a");
    user.setAttribute("href", "/gallery/" + image.username);
    user.classList.add("picture-user");
    picture_div.append(user);

    let pp = document.createElement("div");
    pp.classList.add("picture-pp");
    pp.setAttribute("style", "background-image:url(" + image.pp + ")");
    user.appendChild(pp);

    let username = document.createElement("div");
    username.innerText = image.username;
    username.classList.add("picture-username");
    user.appendChild(username);

    let title = document.createElement("div");
    title.innerText = image.title;
    title.classList.add("picture-title");
    picture_div.appendChild(title);

    let form = document.createElement("div");
    form.classList.add("picture-form")
    picture_div.appendChild(form);
    if (type == "sell") {
        let price = document.createElement("input");
        price.classList.add("picture-price")
        price.setAttribute("type", "number");
        price.setAttribute("name", "price");
        price.setAttribute("min", "0");
        form.appendChild(price);

        let algo = document.createElement("div");
        algo.classList.add("algo");
        form.appendChild(algo);

        let submit = document.createElement("button");
        submit.setAttribute("name", "sell");
        submit.innerText = "Sell";
        submit.addEventListener("click", () => {
            sell(image.token_id, price, MainPage);
        })
        form.appendChild(submit);
    } else if (type == "bid") {
        let price = document.createElement("input");
        price.classList.add("picture-bid")
        price.setAttribute("type", "number");
        price.setAttribute("name", "price");
        price.setAttribute("min", image.min_price);
        price.setAttribute("value", image.min_price);
        form.appendChild(price);

        let algo = document.createElement("div");
        algo.classList.add("algo");
        form.appendChild(algo);

        let submit = document.createElement("button");
        submit.setAttribute("name", "bid");
        submit.classList.add("buy-button");
        submit.addEventListener("click", () => {
            bid(image.token_id, price, MainPage);
        });
        submit.innerText = "Bid";
        form.appendChild(submit);

        let countdown = document.createElement("div");
        countdown.classList.add("picture-countdown");
        createCountdown(image.end_date.replace(" ", "T"), countdown);
        picture_div.appendChild(countdown);

    } else if (type == "") {
    } else {
        let price = document.createElement("div");
        price.classList.add("picture-price")
        price.setAttribute("name", "price");
        price.innerText = image.price;
        form.appendChild(price);

        let algo = document.createElement("div");
        algo.classList.add("algo");
        form.appendChild(algo);

        if (type == "cancel") {
            let submit = document.createElement("button");
            submit.setAttribute("type", "submit");
            submit.setAttribute("name", "cancel");
            submit.addEventListener("click", () => {
                cancel(image.token_id, MainPage);
            });
            submit.innerText = "Cancel";
            form.appendChild(submit);
        } else if (type == "buy") {
            let submit = document.createElement("button");
            submit.setAttribute("type", "submit");
            submit.setAttribute("name", "buy");
            submit.classList.add("buy-button");
            submit.addEventListener("click", () => {
                buy(image.token_id, price, MainPage);
            });
            submit.innerText = "Buy";
            form.appendChild(submit);

            let seller = document.createElement("a");
            seller.classList.add("picture-seller");
            seller.innerText = "Sold by: " + image.seller;
            seller.setAttribute("href", "/gallery/"+image.seller);
            picture_div.appendChild(seller);
        } else {
            let countdown = document.createElement("div");
            countdown.classList.add("picture-countdown");
            createCountdown(image.end_date.replace(" ", "T"), countdown);
            picture_div.appendChild(countdown);
        }
    }

    let image_button = document.createElement("button");
    image_button.setAttribute("type", "button");
    image_button.setAttribute("data-toggle", "modal");
    image_button.setAttribute("data-target", "#modal_" + image.token_id);
    image_button.classList.add("img-button");
    image_button.classList.add("picture-photo");
    picture_div.appendChild(image_button);

    var img = new Image()
    img.src = window.URL.createObjectURL(b64toBlob(image.uri, image.extension));
    image_button.appendChild(img);

    addModal(image, page);
}

function displayMore(images, page) {
    if (images.length == 0) {
        if (!displayedFirst[page]) {
            document.getElementById(page + "_div").innerText = Errors[page];
        }
        endPage[page] = true;
        return;
    }
    displayedFirst[page] = true;

    for (let image of images) {
        displayImage(page, image, SubpageType[page]);
    }
}

function requestMore(page) {
    requestedMorePictures[page] = true;
    document.querySelector(".loading").classList.remove("hidden");
    var http = new XMLHttpRequest();
    http.open('POST', "/" + MainPage, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            displayMore(JSON.parse(http.responseText).pictures, page);
        }
        requestedMorePictures[page] = false;
        document.querySelector(".loading").classList.add("hidden");
    }
    http.send("more=" + page);
}

function addModal(image, page) {
    let modal_div = document.createElement("div");
    modal_div.id = "modal_" + image.token_id;
    modal_div.classList.add("modal");
    modal_div.classList.add("fade");
    modal_div.setAttribute("role", "dialog");
    document.getElementById(page+"_div").appendChild(modal_div);

    let modal_content = document.createElement("div");
    modal_content.classList.add("modal-dialog");
    modal_content.classList.add("modal-lg");
    modal_div.appendChild(modal_content);

    let modal_header = document.createElement("div");
    modal_header.classList.add("modal-header");
    modal_content.appendChild(modal_header);

    let close_button = document.createElement("button");
    close_button.setAttribute("type", "button");
    close_button.setAttribute("data-dismiss", "modal");
    close_button.classList.add("close");
    close_button.innerHTML = "&times";
    modal_header.append(close_button);

    let title = document.createElement("h1");
    title.classList.add("modal-title");
    title.innerText = image.title;
    modal_header.append(title);

    let modal_body = document.createElement("div");
    modal_body.classList.add("picture-form")
    modal_content.appendChild(modal_body);

    let img = document.createElement("img");
    img.setAttribute("src", image.uri);
    modal_body.append(img);

    let modal_footer = document.createElement("div");
    modal_footer.classList.add("modal-footer");
    modal_content.appendChild(modal_footer);

    let close_button2 = document.createElement("button");
    close_button2.setAttribute("type", "button");
    close_button2.setAttribute("data-dismiss", "modal");
    close_button2.classList.add("btn");
    close_button2.classList.add("btn-default");
    close_button2.innerHTML = "Close";
    modal_footer.append(close_button2);
}

function b64toBlob(dataURI, extension) {
    var byteString = atob(dataURI.split(',')[1]);
    var ab = new ArrayBuffer(byteString.length);
    var ia = new Uint8Array(ab);

    for (var i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: 'image/' + extension });
}