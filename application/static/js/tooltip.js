function addTooltip(title, text, autoClose = false) {
    let tooltip = document.createElement("div");
    tooltip.classList.add("tooltip");
    document.body.appendChild(tooltip);

    console.log(tooltip);
    let tooltipTitle = document.createElement("div");
    tooltipTitle.classList.add("tooltip-title");
    if (title != "") tooltipTitle.innerText = title;
    tooltip.appendChild(tooltipTitle);

    let tooltipBody = document.createElement("div");
    tooltipBody.classList.add("tooltip-body");
    if (text != "") tooltipBody.innerText = text;
    tooltip.appendChild(tooltipBody);

    if (autoClose) {
        setTimeout(() => {
            tooltip.remove();
        }, 1500);
    } else {
        let closeButton = document.createElement("button");
        closeButton.innerText = "X";
        tooltipTitle.appendChild(closeButton);

        closeButton
            .addEventListener("click", () => {
            tooltip.remove();
        });
    }
}