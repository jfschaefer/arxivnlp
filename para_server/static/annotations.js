
var MATH_TO_INDEX = {};
var INDEX_TO_MATH = [];
var SELECTED = null;
var ANNOTATIONS = {};
var FILENAME = null;
var CONFIG;


async function getParagraph(arg) {
    const response = await fetch('http://127.0.0.1:5000/getParagraph/' + arg);
    const paragraph = await response.json();
    document.getElementById('paragraph').innerHTML = paragraph['html'];
    FILENAME = paragraph['filename'];
    ANNOTATIONS = paragraph['annotations'];
    initMathwrappers();
}

async function storeAnnotations() {
    const response = await fetch('http://127.0.0.1:5000/storeAnnos/' + FILENAME, {
        method: 'PUT',
        body: JSON.stringify(ANNOTATIONS),
        headers: { 'Content-Type': 'application/json' }
    });
    document.getElementById('savebutton').classList = ['button success'];
}


function annotate(tag) {
    if (SELECTED != null) {
        ANNOTATIONS[SELECTED] = tag;
        document.getElementById(SELECTED + '.wrapper').classList = [tag];
        document.getElementById('savebutton').classList = ['button save'];
    }
}

function initMathwrappers() {
    MATH_TO_INDEX = {};
    INDEX_TO_MATH = [];
    SELECTED = null;
    const mathnodes = document.evaluate("//*[name()='math' or contains(@class, 'ltx_equation') or contains(@class,'ltx_equationgroup')]",
                                        document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    console.log("Initializing " + mathnodes.snapshotLength + " math nodes");
    for (let i = 0; i < mathnodes.snapshotLength; i++) {
        // check if a parent has already been selected
        const mathnode = mathnodes.snapshotItem(i);
        var parentnode = mathnode.parentNode;
        var isOkay = true;
        console.log("Checking for " + mathnode.id + "   - " + parentnode);
        while (isOkay && parentnode != null) {
            console.log("Checking " + parentnode.id);
            if (ANNOTATIONS.hasOwnProperty(parentnode.id)) {
                isOkay = false;
            } else {
                parentnode = parentnode.parentNode;
            }
        }
        if (!isOkay) continue;


        MATH_TO_INDEX[mathnode.id] = i;
        INDEX_TO_MATH[i] = mathnode.id;

        var mathwrapper;
        if (mathnode.tagName != "math") {
            mathwrapper = document.createElement('div');
        } else {
            mathnode.setAttribute("display", "inline");    // some math nodes have display="block", which interferes with background colors
            mathwrapper = document.createElement('span');
        }

        mathwrapper.id = mathnode.id + '.wrapper';
        mathwrapper.onclick = function () { mathSelect(mathnode.id) };
        if (!ANNOTATIONS.hasOwnProperty(mathnode.id)) {
            ANNOTATIONS[mathnode.id] = DEFAULTTAG;
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

window.addEventListener("keydown", function (event) {
    if (event.key == "n") {
        prevOrNext(1);
    } else if (event.key == "N") {
        prevOrNext(-1);
    } else if (event.key == "s") {
        storeAnnotations();
    } else {
        for (const k of CONFIG.tags) {
            if (event.key == k.key) {
                annotate(k.id);
                break;
            }
        }
    }
});
// window.onload = initMathwrappers();
