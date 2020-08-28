function convertObjectToSvg() {
    let innerSvg = obj.contentDocument.querySelector("svg");
    document.querySelector(".map").appendChild(innerSvg);
    obj.parentNode.removeChild(obj);
}

function addPuysToSvg() {
    let puyGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    for (let i = 0; i < WAYPOINTS.length; i++) {
        let waypoint = WAYPOINTS[i];
        let group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.className = "puy";
        let circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", waypoint.x);
        circle.setAttribute("cy", waypoint.y);
        circle.setAttribute("r", 3);
        circle.setAttribute("stroke", "black");
        if (waypoint.visited) {
            circle.setAttribute("fill", "rgba(50, 50, 255, 1)");
        } else {
            circle.setAttribute("fill", "rgba(255, 50, 50, 1)");
        }
        let text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", waypoint.x);
        text.setAttribute("y", waypoint.y);
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("stroke", "white");
        text.setAttribute("dy", -7);
        text.innerHTML = waypoint.label;
        group.appendChild(circle);
        group.appendChild(text);
        puyGroup.appendChild(group);
    }
    document.querySelector("#scene").appendChild(puyGroup);
}

function panzoomSetup() {
    let instance = panzoom(document.querySelector("#scene"));
    instance.setTransformOrigin(null);
}

let obj = document.getElementById("svgObject");
obj.addEventListener("load", (event) => {
    console.log("SVG object is loaded");
    convertObjectToSvg();
    console.log("SVG object has been inserted as SVG inside the DOM");
    addPuysToSvg();
    console.log("Puys have been added to the SVG");
    panzoomSetup();
    console.log("Panzoom is initialized");
});

document.querySelector("#about_button").addEventListener("click", (event) => {
    let button = document.querySelector("#about_button");
    let content = document.querySelector("#about_content");
    if (content.classList.contains("show")) {
        content.classList.remove("show");
        button.innerHTML = "[à propos]";
    } else {
        content.classList.add("show");
        button.innerHTML = "[fermer]";
        let listContent = document.querySelector("#list_content");
        if (listContent.classList.contains("show")) {
            listContent.classList.remove("show");
            document.querySelector("#list_button").innerHTML = "[liste]";
        }
    }
});
document.querySelector("#list_button").addEventListener("click", (event) => {
    let button = document.querySelector("#list_button");
    let content = document.querySelector("#list_content");
    if (content.classList.contains("show")) {
        content.classList.remove("show");
        button.innerHTML = "[liste]";
    } else {
        content.classList.add("show");
        button.innerHTML = "[fermer]";
        let aboutContent = document.querySelector("#about_content");
        if (aboutContent.classList.contains("show")) {
            aboutContent.classList.remove("show");
            document.querySelector("#about_button").innerHTML = "[à propos]";
        }
    }
});
