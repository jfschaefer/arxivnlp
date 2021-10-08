const DOCID = "1808.02342";
const HOSTURL = "http://127.0.0.1:5000"

const OPTIONS = {
    "U" : {     // unannotated
        "name" : "U",
        "color" : "#ff0",
    },
    "P" : {     // problematic
        "name" : "P",
        "color" : "#f00",
    },
    "NUM" : {     // number
        "name" : "NUM",
        "color" : "#fa0",
    },
    "CL" : {    // clause
        "name" : "CL",
        "color" : "#88f",
    },
    "ID" : {     // identifier
        "name" : "ID",
        "color" : "#0fa",
    },
};

function loadStyle() {
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

#save {
    padding: 0.5cm;
    opacity: 0.9;
    background-color: gray;
    font-size: 48pt;
    position: fixed;
    top: 0cm;
    right: 0cm;
}
`;
    for (const [key, value] of Object.entries(OPTIONS)) {
        styleSheet.innerText += "." + key + " { background-color: " + value["color"] + "; }\n";
    }

    document.head.appendChild(styleSheet);
}


var ANNOTATIONS = {}

async function loadAnnotations() {
    const response = await fetch(HOSTURL + '/getAnnotations/' + DOCID);
    ANNOTATIONS = await response.json();
}

async function storeAnnotations() {
    const response = await fetch(HOSTURL + '/storeAnnotations/' + DOCID, {
        method: 'PUT',
        body: JSON.stringify(ANNOTATIONS),
        headers: { 'Content-Type': 'application/json' }
    });
}

var LAST_CLICKED = "";

async function init() {
    loadStyle();
    await loadAnnotations();

    // INITIALIZE MATH NODES
    const mathnodes = document.evaluate("//*[name()='math']", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    console.log("Initializing " + mathnodes.snapshotLength + " math nodes");
    for (let i = 0; i < mathnodes.snapshotLength; i++) {
        const mathnode = mathnodes.snapshotItem(i);
        mathnode.setAttribute("display", "inline");    // some math nodes have display="block", which interferes with background colors

        const popupcontainer = document.createElement('span');
        popupcontainer.onclick = function () { openPopup(mathnode.id) };
        if (!ANNOTATIONS.hasOwnProperty(mathnode.id)) {
            ANNOTATIONS[mathnode.id] = "U";
        }
        popupcontainer.classList.add(ANNOTATIONS[mathnode.id]);
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

    const savebutton = document.createElement('span');
    savebutton.id = "save";
    savebutton.style.color = "#0f0";
    savebutton.textContent = "SAVE";
    savebutton.onclick = function () { storeAnnotations().then(_ => savebutton.style.color="#0f0")};
    document.body.appendChild(savebutton);


    // support keyboard input
    window.addEventListener("keydown", function (event) {
        switch (event.key) {
            case "1": maybeSelect("ID"); break;
            case "2": maybeSelect("CL"); break;
            case "3": maybeSelect("NUM"); break;
            case "4": maybeSelect("P"); break;
            case "5": maybeSelect("U"); break;
            case "s": storeAnnotations().then(_ => savebutton.style.color="#0f0"); break;
        }
    });

    console.log("Finished Initialization");
}

function openPopup(mathid) {
    const popup = document.getElementById(mathid + ".popup");
    if (popup.style.visibility == "visible") {
        popup.style.visibility = "hidden";
    } else {
        popup.style.visibility = "visible";
    }
    LAST_CLICKED = mathid;
}

function optionSelect(mathid, value) {
    const popupnode = document.getElementById(mathid + ".popup");
    popupnode.parentNode.classList = value;
    ANNOTATIONS[mathid] = value;
    const savebutton = document.getElementById("save");
    savebutton.style.color = "#f00";
    LAST_CLICKED = "";
}

function maybeSelect(value) {
    if (LAST_CLICKED != "") {
        const popupnode = document.getElementById(LAST_CLICKED + ".popup");
        popupnode.style.visibility = "hidden";
        optionSelect(LAST_CLICKED, value);
    }
}


init();
