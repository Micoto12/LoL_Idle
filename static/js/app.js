function startGame() {
    fetch('/api/start_game')
        .then(response => response.json())
        .then(data => {
            document.getElementById('result').innerText = "Игра началась! Введите имя чемпиона.";
            document.getElementById('startGameBtn').style.display = "none";   // Скрыть кнопку "Новая игра"
            document.getElementById('guessBtn').style.display = "inline";     // Показать кнопку "Guess"
            document.getElementById('guessInput').value = "";                 // Очистить поле ввода
        });
}

function sendGuess() {
    const guess = document.getElementById('guessInput').value;
    fetch('/api/guess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: guess })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else if (data.result === "correct") {
            document.getElementById('result').innerText = `Правильно! Попыток: ${data.attempts}`;
            document.getElementById('guessBtn').style.display = "none";      // Скрыть кнопку "Guess"
            document.getElementById('startGameBtn').style.display = "inline"; // Показать "Новая игра"
        } else {
            document.getElementById('result').innerHTML =
            `Неправильно!<br>Подсказки:<ul>` +
            data.hints.map(hint => `<li>${hint}</li>`).join('') +
            `</ul>(Попыток: ${data.attempts})`;
        }
    });
}

// При загрузке страницы показываем только кнопку "Новая игра"
window.onload = function() {
    document.getElementById('startGameBtn').style.display = "inline";
    document.getElementById('guessBtn').style.display = "none";
};