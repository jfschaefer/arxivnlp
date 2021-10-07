const OPTIONS = {
    "U" : {     // unannotated
        "name" : "U",
        "color" : "#ff0",
    },
    "P" : {     // problematic
        "name" : "P",
        "color" : "#f00",
    },
    "Cl" : {    // clause
        "name" : "Cl",
        "color" : "#88f",
    },
    "N" : {     // noun
        "name" : "N",
        "color" : "#0fa",
    },
    "PN" : {     // proper noun
        "name" : "PN",
        "color" : "#fa0",
    },
};


function init() {
    // LOAD STYLE
    const styleSheet = document.createElement("style");
    styleSheet.innerText = `
.popupbox {
    visibility: hidden;
    // background-color: #555;
    color: #000;
    text-align: center;
    position: absolute;
    top: -4cm;
    right: 0.1cm;
    z-index: 5;
    width: 2cm;
}
.popupoption {
    display: inline-block;
    width: 1.5cm;
    height: 0.7cm;
}
.popupbox .show {
    visibility: visible;
}
`;
    for (const [key, value] of Object.entries(OPTIONS)) {
        styleSheet.innerText += "." + key + " { background-color: " + value["color"] + "; }\n";
    }

    document.head.appendChild(styleSheet);


    // INITIALIZE MATH NODES
    const mathnodes = document.evaluate("//*[name()='math']", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    console.log("Initializing " + mathnodes.snapshotLength + " math nodes");
    for (let i = 0; i < mathnodes.snapshotLength; i++) {
        const mathnode = mathnodes.snapshotItem(i);
        mathnode.setAttribute("display", "inline");    // some math nodes have display="block", which interferes with background colors

        const popupcontainer = document.createElement('span');
        popupcontainer.onclick = function () { openPopup(mathnode.id) };
        popupcontainer.classList.add("U");
        popupcontainer.style.position = "relative";
        
        const popup = document.createElement('span');
        popup.innerHTML = "";
        for (const [key, value] of Object.entries(OPTIONS)) {
            popup.innerHTML += "<span class='popupoption " + key + "' onclick='optionSelect(\"" + mathnode.id + "\", \"" + key + "\")'>" + value["name"] + "</span>";
        }

        popup.id = mathnode.id + ".popup";
        popup.classList.add("popupbox");
        popupcontainer.appendChild(popup);
        
        mathnode.parentNode.insertBefore(popupcontainer, mathnode);
        popupcontainer.appendChild(mathnode);
    }

    console.log("Finished Initialization");
}

function openPopup(mathid) {
    const popup = document.getElementById(mathid + ".popup");
    if (popup.style.visibility == "visible") {
        popup.style.visibility = "hidden";
    } else {
        popup.style.visibility = "visible";
    }
}

function optionSelect(mathid, value) {
    const popupnode = document.getElementById(mathid + ".popup");
    popupnode.parentNode.classList = value;
}


init();