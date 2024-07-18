document.addEventListener("DOMContentLoaded", function() {
    let squares = document.querySelectorAll(".chess-board div");
    squares.forEach((square, index) => {
        document.querySelector("#betzaSubmit").addEventListener("click", function() {
            let betza = document.querySelector("#betzaInput");
            fetch('/get_betza/' + betza.value)
                .then(response => response.json())
                .then(data => {
                    squares.forEach(square => square.classList.remove("highlight"));
                    data.forEach(i => squares[(7 - Math.floor(i / 8)) * 8 + i % 8].classList.add("highlight")); // Correct for board orientation
                });
        });
        square.addEventListener("click", function() {
            if (square.classList.contains("selected")) {
                square.classList.remove("selected");
            } else {
                square.classList.add("selected");
            }
            if (square.classList.contains("highlight")) {
                // Move the piece and update the board
                fetch('/make_move/' + index, {
                        method: 'POST'
                    })
                    .then(response => response.json())
                    .then(fen => {
                        squares.forEach(square => {
                            square.classList.remove("highlight");
                            let img = square.querySelector("img");
                            if (img) img.remove();
                        });
                        fen.split(" ")[0].split("/").forEach((row, i) => {
                            row.replace(/\d/g, m => " ".repeat(m)).split("").forEach((cell, j) => {
                                if (cell !== " ") {
                                    let img = document.createElement("img");
                                    img.src = `/static/pieces/${cell === cell.toUpperCase() ? 'w' : 'b'}${cell.toLowerCase()}.png`;
                                    squares[8 * i + j].appendChild(img);
                                }
                            });
                        });
                    });
            } else {
                fetch('/legal_moves/' + index)
                    .then(response => response.json())
                    .then(data => {
                        squares.forEach(square => square.classList.remove("highlight"));
                        data.forEach(i => squares[(7 - Math.floor(i / 8)) * 8 + i % 8].classList.add("highlight")); // Correct for board orientation
                    });
            }
        });
    });
});