let usedChampions = [];
const guessInput = document.getElementById('guessInput');
const autocompleteList = document.getElementById('autocomplete-list');

function startGame() {
    usedChampions = [];
    localStorage.removeItem('usedChampions');
    fetch('/api/start_game')
        .then(response => response.json())
        .then(data => {
            document.getElementById('game-message').innerText = "Игра началась! Введите имя чемпиона.";
            document.getElementById('result').innerText = "";
            document.getElementById('startGameBtn').style.display = "none";
            document.getElementById('guessBtn').style.display = "inline";
            document.getElementById('guessInput').value = "";
            document.getElementById('guess-block').style.display = 'flex';
            handleNewGameStart();
        });
}

function sendGuess() {
    const guessInput = document.getElementById('guessInput');
    const guess = guessInput.value.trim();

    fetch('/api/guess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: guess })
    })
    .then(response => response.json())
    .then(data => {
        guessInput.value = "";
        if (data.error) {
            alert(data.error);
        } else {
            // Добавляем в список использованных
            if (data.accepted_name) {
                usedChampions.push(data.accepted_name);
            } else {
                usedChampions.push(guess);
            }
            saveUsedChampions();
            updateAutocompleteSource();

            if (data.result === "correct") {
                document.getElementById('result').innerText = `Правильно! Попыток: ${data.attempts}`;
                document.getElementById('guessBtn').style.display = "none";
                document.getElementById('startGameBtn').style.display = "inline";
                handleNewGameStart();
            } else {
                document.getElementById('result').innerHTML =
                    `Неправильно!<br>Подсказки:<ul>` +
                    data.hints.map(hint => `<li>${hint}</li>`).join('') +
                    `</ul>(Попыток: ${data.attempts})`;
            }
            //console.log('usedChampions:', usedChampions);
        }
    });
}

function fetchAutocompleteSuggestions(query, callback) {
    const used = usedChampions.join(',');
    fetch(`/autocomplete?q=${encodeURIComponent(query)}&used=${encodeURIComponent(used)}`)
        .then(response => response.json())
        .then(data => callback(data));
}

function handleNewGameStart() {
    usedChampions = [];
    localStorage.removeItem('usedChampions'); // если используешь localStorage
    updateAutocompleteSource();
}

function saveUsedChampions() {
    localStorage.setItem('usedChampions', JSON.stringify(usedChampions));
}

function loadUsedChampions() {
    const data = localStorage.getItem('usedChampions');
    if (data) {
        usedChampions = JSON.parse(data);
    } else {
        usedChampions = [];
    }
}

function updateAutocompleteSource() {
    const query = guessInput.value.trim();
    if (query.length < 1) {
        autocompleteList.innerHTML = '';
        return;
    }
    fetchAutocompleteSuggestions(query, function(suggestions) {
        autocompleteList.innerHTML = '';
        suggestions.forEach(name => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.innerText = name;
            item.onclick = function() {
                guessInput.value = name;
                autocompleteList.innerHTML = '';
            };
            autocompleteList.appendChild(item);
        });
    });
}


function showGameInterface(attempts = 0) {
    document.getElementById('game-message').innerText = "Игра продолжается! Введите имя чемпиона.";
    document.getElementById('result').innerText = attempts > 0 ? `Попыток: ${attempts}` : "";
    document.getElementById('startGameBtn').style.display = "none";
    document.getElementById('guessBtn').style.display = "inline";
    document.getElementById('guessInput').value = "";
    document.getElementById('guess-block').style.display = 'flex';
}

function showStartButton() {
    document.getElementById('startGameBtn').style.display = "inline";
    document.getElementById('guess-block').style.display = 'none';
    document.getElementById('guessBtn').style.display = "none";
    document.getElementById('game-message').innerText = "";
    document.getElementById('result').innerText = "";
}

function resetUsedChampions() {
    fetch('/admin/reset_used', {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            document.getElementById('admin-info').innerText = 'Список использованных чемпионов сброшен!';
        });
}

function resetAttempts() {
    fetch('/admin/reset_attempts', {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            document.getElementById('admin-info').innerText = 'Попытки сброшены!';
        });
}

function showTargetChampion() {
    fetch('/admin/show_target')
        .then(r => r.json())
        .then(data => {
            document.getElementById('admin-info').innerText = 'Угадываемый чемпион: ' + (data.target_name || 'нет');
        });
}

guessInput.addEventListener('input', function() {
    const query = this.value.trim();
    if (query.length < 1) {
        autocompleteList.innerHTML = '';
        return;
    }
    fetchAutocompleteSuggestions(query, function(suggestions) {
        autocompleteList.innerHTML = '';
        suggestions.forEach(name => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.innerText = name;
            item.onclick = function() {
                guessInput.value = name;
                autocompleteList.innerHTML = '';
            };
            autocompleteList.appendChild(item);
        });
    });
});

// При загрузке страницы показываем только кнопку "Новая игра"
window.onload = function() {
    loadUsedChampions();
    // Проверяем статус игры при загрузке страницы
    fetch('/api/game_status')
        .then(response => response.json())
        .then(data => {
            if (data.in_progress) {
                showGameInterface(data.attempts);
            } else {
                showStartButton();
            }
        });

    document.getElementById('startGameBtn').addEventListener('click', startGame);
    //document.getElementById('guessBtn').addEventListener('click', sendGuess);

    document.getElementById('guessInput').addEventListener('keydown', function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            document.getElementById('guessBtn').click();
        }
    });

    document.getElementById('guessForm').addEventListener('submit', function(event) {
        event.preventDefault();
        sendGuess();
    });
};