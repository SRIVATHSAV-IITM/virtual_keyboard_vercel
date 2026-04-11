document.addEventListener('DOMContentLoaded', () => {
    const levelSelectionElement = document.getElementById('level-selection');
    const gameContainerElement = document.getElementById('game-container');
    const boardElement = document.getElementById('game-board');
    const winningMessageElement = document.getElementById('winning-message');
    const winningMessageTextElement = document.querySelector('[data-winning-message-text]');
    const newGameButton = document.getElementById('newGameButton');
    const exitButton = document.getElementById('exitButton');
    const closeButton = document.getElementById('closeButton');
    const levelButtons = document.querySelectorAll('.level-btn');

    const X_CLASS = 'x';
    const CIRCLE_CLASS = 'circle';
    const WINNING_COMBINATIONS = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6]
    ];

    let circleTurn;
    let currentLevel;
    let cellElements;

    const startGame = (level) => {
        currentLevel = level;
        levelSelectionElement.classList.add('hidden');
        gameContainerElement.classList.remove('hidden');
        winningMessageElement.classList.add('hidden');
        circleTurn = false;
        createBoard();
    };

    const createBoard = () => {
        boardElement.innerHTML = '';
        cellElements = [];
        for (let i = 0; i < 9; i++) {
            const cell = document.createElement('div');
            cell.classList.add('cell');
            cell.dataset.cellIndex = i;
            cell.addEventListener('click', handleClick, { once: true });
            boardElement.appendChild(cell);
            cellElements.push(cell);
        }
    };

    const handleClick = (e) => {
        const cell = e.target;
        const currentClass = circleTurn ? CIRCLE_CLASS : X_CLASS;
        placeMark(cell, currentClass);
        if (checkWin(currentClass)) {
            endGame(false);
        } else if (isDraw()) {
            endGame(true);
        } else {
            swapTurns();
            if (circleTurn) {
                setTimeout(aiMove, 500);
            }
        }
    };

    const placeMark = (cell, currentClass) => {
        cell.classList.add(currentClass);
    };

    const swapTurns = () => {
        circleTurn = !circleTurn;
    };

    const checkWin = (currentClass) => {
        return WINNING_COMBINATIONS.some(combination => {
            return combination.every(index => {
                return cellElements[index].classList.contains(currentClass);
            });
        });
    };

    const isDraw = () => {
        return [...cellElements].every(cell => {
            return cell.classList.contains(X_CLASS) || cell.classList.contains(CIRCLE_CLASS);
        });
    };

    const endGame = (draw) => {
        if (draw) {
            winningMessageTextElement.innerText = 'Draw!';
        } else {
            winningMessageTextElement.innerText = `${circleTurn ? "O's" : "X's"} Wins!`;
            highlightWinningCells();
        }
        winningMessageElement.classList.remove('hidden');
        gameContainerElement.classList.add('hidden');
        setTimeout(() => window.close(), 3000); // Close after 3 seconds
    };

    const highlightWinningCells = () => {
        const winningCombination = WINNING_COMBINATIONS.find(combination => {
            return combination.every(index => {
                return cellElements[index].classList.contains(circleTurn ? CIRCLE_CLASS : X_CLASS);
            });
        });
        if (winningCombination) {
            winningCombination.forEach(index => {
                cellElements[index].classList.add('win');
            });
        }
    };

    const resetGame = () => {
        levelSelectionElement.classList.remove('hidden');
        gameContainerElement.classList.add('hidden');
        winningMessageElement.classList.add('hidden');
    };

    const aiMove = () => {
        const availableCells = [...cellElements].filter(
            cell => !cell.classList.contains(X_CLASS) && !cell.classList.contains(CIRCLE_CLASS)
        );

        let moveCell;

        if (currentLevel === 'easy') {
            moveCell = availableCells[Math.floor(Math.random() * availableCells.length)];
        } else {
            const bestMoveIndex = findBestMove(isHard());
            moveCell = cellElements[bestMoveIndex];
        }

        if (moveCell) {
            placeMark(moveCell, CIRCLE_CLASS);
            if (checkWin(CIRCLE_CLASS)) {
                endGame(false);
            } else if (isDraw()) {
                endGame(true);
            } else {
                swapTurns();
            }
        }
    };

    const isHard = () => currentLevel === 'hard';

    const findBestMove = () => {
        let bestScore = -Infinity;
        let move;

        cellElements.forEach((cell, index) => {
            if (!cell.classList.contains(X_CLASS) && !cell.classList.contains(CIRCLE_CLASS)) {
                cell.classList.add(CIRCLE_CLASS);
                let score = minimax(0, false);
                cell.classList.remove(CIRCLE_CLASS);
                if (score > bestScore) {
                    bestScore = score;
                    move = index;
                }
            }
        });
        return move;
    };

    const minimax = (depth, isMaximizing) => {
        if (checkWin(CIRCLE_CLASS)) return 10 - depth;
        if (checkWin(X_CLASS)) return depth - 10;
        if (isDraw()) return 0;

        if (isMaximizing) {
            let bestScore = -Infinity;
            cellElements.forEach(cell => {
                if (!cell.classList.contains(X_CLASS) && !cell.classList.contains(CIRCLE_CLASS)) {
                    cell.classList.add(CIRCLE_CLASS);
                    let score = minimax(depth + 1, false);
                    cell.classList.remove(CIRCLE_CLASS);
                    bestScore = Math.max(score, bestScore);
                }
            });
            return bestScore;
        } else {
            let bestScore = Infinity;
            cellElements.forEach(cell => {
                if (!cell.classList.contains(X_CLASS) && !cell.classList.contains(CIRCLE_CLASS)) {
                    cell.classList.add(X_CLASS);
                    let score = minimax(depth + 1, true);
                    cell.classList.remove(X_CLASS);
                    bestScore = Math.min(score, bestScore);
                }
            });
            return bestScore;
        }
    };

    levelButtons.forEach(button => {
        button.addEventListener('click', () => startGame(button.dataset.level));
    });

    newGameButton.addEventListener('click', () => startGame(currentLevel));
    exitButton.addEventListener('click', () => window.close());
    closeButton.addEventListener('click', () => window.close());
});
