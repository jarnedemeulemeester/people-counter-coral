var buttonVideoStats = document.getElementById("Videostats");
var buttonBbox = document.getElementById("Bbox");
var buttonAccuracy = document.getElementById("Accuracy");
var buttonCrossing = document.getElementById("Crossing");

buttonVideoStats.onclick = function() {
    console.log("Button VideoStats - pressed")

    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            // alert(xhr.responseText);
        }
    }
    // XMLHttpRequest
    xhr.open("POST", "/toggle");
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.send(JSON.stringify({ toggle: "VideoStats" }));
};
buttonBbox.onclick = function() {
    console.log("Button Bbox - pressed ")

    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            // alert(xhr.responseText);
        }
    }
    // XMLHttpRequest
    xhr.open("POST", "/toggle");
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.send(JSON.stringify({ toggle: "Bbox" }));
};
buttonAccuracy.onclick = function() {
    console.log("Button Accuracy - pressed ")

    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            // alert(xhr.responseText);
        }
    }
    // XMLHttpRequest
    xhr.open("POST", "/toggle");
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.send(JSON.stringify({ toggle: "Accuracy" }));
};

buttonCrossing.onclick = function() {
    console.log("Button Crossing - pressed")

    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            // alert(xhr.responseText);
        }
    }
    // XMLHttpRequest
    xhr.open("POST", "/toggle");
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.send(JSON.stringify({ toggle: "Crossing" }));
};

