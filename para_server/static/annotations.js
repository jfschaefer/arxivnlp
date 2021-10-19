
var MATH_TO_INDEX = {};
var INDEX_TO_MATH = [];
var SELECTED = null;
var ANNOTATIONS = {};
var FILENAME = null;


async function next() {
    const response = await fetch('http://127.0.0.1:5000/getRandomParagraph');
    const paragraph = await response.json();
    document.getElementById('paragraph').innerHTML = paragraph['html'];
    FILENAME = paragraph['filename'];
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
    ANNOTATIONS = {};
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

// window.onload = initMathwrappers();