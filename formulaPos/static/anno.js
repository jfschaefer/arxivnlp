
// TODO: These should be generated by the server
const DOCID = "1808.02342";
const HOSTURL = "http://127.0.0.1:5000"


var SELECTED = null;

const OPTIONS = {
    "U" : {     // unannotated
        "name" : "U",
        "color" : "#ff0",
        "key": "5",         // Warning: currently loadKeyboardShortcuts also has to be adjusted
    },
    "P" : {     // problematic
        "name" : "P",
        "color" : "#f00",
        "key": "4",
    },
    "NUM" : {     // number
        "name" : "NUM",
        "color" : "#fa0",
        "key": "3",
    },
    "CL" : {    // clause
        "name" : "CL",
        "color" : "#88f",
        "key": "2",
    },
    "ID" : {     // identifier
        "name" : "ID",
        "color" : "#0fa",
        "key": "1",
    },
};

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

function loadCSS() {
    // static
    const linknode = document.createElement('link');
    linknode.setAttribute('rel', 'stylesheet');
    linknode.setAttribute('href', '/static/anno.css');
    document.head.appendChild(linknode);

    // background color for options
    const styleSheet = document.createElement("style");
    for (const [key, value] of Object.entries(OPTIONS)) {
        styleSheet.innerText += "." + key + " { background-color: " + value["color"] + "; }\n";
    }
    document.head.appendChild(styleSheet);
}

function makeSidebar() {
    const mainpage = document.evaluate("//div[@class='ltx_page_main']", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    if (mainpage == null) { alert("Failed to find .ltx_page_main"); }
    const wrapper = document.createElement('div');
    wrapper.id = "documentwrapper";
    const sidebar = document.createElement('div');

    sidebar.id = "sidebarwrapper";
    var content = "<div id='sidebar'><div class='sidebarElement' id='savebutton' onclick='storeAnnotations().then(_ => savebutton.style.color=\"#0f0\");')>SAVE<sup>s</sup></div>";
    for (const [key, value] of Object.entries(OPTIONS)) {
        content += "<span class='sidebarElement " + key + "' onclick='optionSelect(\"" + key + "\")'>" + value["name"] + "<sup>" + value["key"] + "</sup>" + "</span>";
    }
    content += "</div>";
    sidebar.innerHTML = content;

    mainpage.parentNode.insertBefore(wrapper, mainpage);
    wrapper.appendChild(sidebar);
    wrapper.appendChild(mainpage);
}

MATH_TO_INDEX = {};
INDEX_TO_MATH = [];

function initMathwrappers() {
    const mathnodes = document.evaluate("//*[name()='math']", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    console.log("Initializing " + mathnodes.snapshotLength + " math nodes");
    for (let i = 0; i < mathnodes.snapshotLength; i++) {
        const mathnode = mathnodes.snapshotItem(i);
        MATH_TO_INDEX[mathnode.id] = i;
        INDEX_TO_MATH[i] = mathnode.id;
        mathnode.setAttribute("display", "inline");    // some math nodes have display="block", which interferes with background colors

        const mathwrapper = document.createElement('span');
        mathwrapper.id = mathnode.id + '.wrapper';
        mathwrapper.onclick = function () { mathSelect(mathnode.id) };
        if (!ANNOTATIONS.hasOwnProperty(mathnode.id)) {
            ANNOTATIONS[mathnode.id] = "U";
        }
        mathwrapper.classList.add(ANNOTATIONS[mathnode.id]);
        mathwrapper.style.position = "relative";

        mathnode.parentNode.insertBefore(mathwrapper, mathnode);
        mathwrapper.appendChild(mathnode);
    }
}

function mathSelect(mathid, scrollTo=false) {
    mathUnselect();
    console.log("selected: " + mathid)
    SELECTED = mathid;
    const wrapper = document.getElementById(mathid + ".wrapper");
    wrapper.classList.add("selected");
    if (scrollTo) {
        window.scrollTo(0, wrapper.getBoundingClientRect().top + window.scrollY - 0.5 * window.innerHeight);
    }
}

function mathUnselect() {
    if (SELECTED != null) {
        const wrapper = document.getElementById(SELECTED + ".wrapper");
        wrapper.classList.remove("selected");
        SELECTED = null;
    }
}

function optionSelect(value) {
    if (SELECTED != null) {
        const wrapper = document.getElementById(SELECTED + ".wrapper");
        wrapper.classList.replace(ANNOTATIONS[SELECTED], value);
        ANNOTATIONS[SELECTED] = value;
        const savebutton = document.getElementById("savebutton");
        savebutton.style.color = "#f00";
    }
}

function prevOrNext(offset) {
    if (SELECTED == null) {
        mathSelect(INDEX_TO_MATH[0], true);
        return;
    }
    var index = MATH_TO_INDEX[SELECTED];
    index = index + offset;
    if (index < 0) { index = INDEX_TO_MATH.length - 1; }
    else if (index >= INDEX_TO_MATH.length) { index = 0; }
    mathUnselect();
    mathSelect(INDEX_TO_MATH[index], true);
}

function loadKeyboardShortcuts() {
    // support keyboard input
    const savebutton = document.getElementById("savebutton");
    window.addEventListener("keydown", function (event) {
        switch (event.key) {
            // TODO: take shortcuts from OPTIONS
            case "1": optionSelect("ID"); break;
            case "2": optionSelect("CL"); break;
            case "3": optionSelect("NUM"); break;
            case "4": optionSelect("P"); break;
            case "5": optionSelect("U"); break;
            case "s": storeAnnotations().then(_ => savebutton.style.color="#0f0"); break;
            case "n": prevOrNext(1); break;
            case "N": prevOrNext(-1); break;
        }
    });
}

async function init() {
    loadCSS();
    makeSidebar();
    await loadAnnotations();
    initMathwrappers();
    loadKeyboardShortcuts();
}


// document.onload = init;
init();