function displayBetza(betza, group) {
    let squares = document.querySelectorAll(".chess-board div");
    fetch('/get_betza/' + betza)
        .then(response => response.json())
        .then(data => {
            data.forEach(i => squares[(7 - Math.floor(i / 8)) * 8 + i % 8].classList.add(group)); // Correct for board orientation
        });
}
function clearDisplay() {
    let squares = document.querySelectorAll(".chess-board div");
    // squares.forEach(square => square.classList.remove("highlight"));
    squares.forEach(square => square.classList.remove("selected"));
}
function changeTempBetza(temp, type) {
    let move_range = document.getElementById("customRange");
    let modifier = document.getElementById("customMod");
    
    if (type == 0) {
        move_range.innerHTML = "";
        modifier.innerHTML = "";
    }
    else if (type == 1) move_range.innerHTML = temp;
    else if (type == 2) modifier.innerHTML += temp;

    let betza_str = modifier.innerHTML + move_range.innerHTML;
    clearDisplay();
    displayBetza(betza_str, "selected");
    // fetch('/get_betza/' + betza_str)
    //     .then(response => response.json())
    //     .then(data => {
    //         // squares.forEach(square => square.classList.remove("highlight"));
    //         data.forEach(i => squares[(7 - Math.floor(i / 8)) * 8 + i % 8].classList.add("selected")); // Correct for board orientation
    //     });
}

function submitTempBetza() {
    let move_range = document.getElementById("customRange");
    let modifier = document.getElementById("customMod");
    let full_betza = document.getElementById("betzaSubmit");

    let betza_str = modifier.innerHTML + move_range.innerHTML;
    move_range.innerHTML = "";
    modifier.innerHTML = "";

    full_betza.value += betza_str;
    clearDisplay();
    displayBetza(full_betza.value, "highlight");
}

document.addEventListener("DOMContentLoaded", function() {
    let squares = document.querySelectorAll(".chess-board div");
    squares.forEach((square, index) => {
        document.querySelector("#betzaSubmit").addEventListener("click", function() {
            displayBetza(document.querySelector("#betzaInput").value, "highlight");
        });
        // square.addEventListener("click", function() {
        //     if (square.classList.contains("selected")) {
        //         square.classList.remove("selected");
        //     } else {
        //         square.classList.add("selected");
        //     }
        //     if (square.classList.contains("highlight")) {
        //         // Move the piece and update the board
        //         fetch('/make_move/' + index, {
        //                 method: 'POST'
        //             })
        //             .then(response => response.json())
        //             .then(fen => {
        //                 squares.forEach(square => {
        //                     square.classList.remove("highlight");
        //                     let img = square.querySelector("img");
        //                     if (img) img.remove();
        //                 });
        //                 fen.split(" ")[0].split("/").forEach((row, i) => {
        //                     row.replace(/\d/g, m => " ".repeat(m)).split("").forEach((cell, j) => {
        //                         if (cell !== " ") {
        //                             let img = document.createElement("img");
        //                             img.src = `/static/pieces/${cell === cell.toUpperCase() ? 'w' : 'b'}${cell.toLowerCase()}.png`;
        //                             squares[8 * i + j].appendChild(img);
        //                         }
        //                     });
        //                 });
        //             });
        //     } else {
        //         fetch('/legal_moves/' + index)
        //             .then(response => response.json())
        //             .then(data => {
        //                 squares.forEach(square => square.classList.remove("highlight"));
        //                 data.forEach(i => squares[(7 - Math.floor(i / 8)) * 8 + i % 8].classList.add("highlight")); // Correct for board orientation
        //             });
        //     }
        // });
    });
});