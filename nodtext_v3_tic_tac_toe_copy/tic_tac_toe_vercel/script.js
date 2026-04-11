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
    const gazePointer = document.getElementById('gaze-pointer');
    const videoElement = document.getElementById('webcam');

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

    const DWELL_DURATION = 1200; // 1.2 seconds
    let circleTurn;
    let currentLevel;
    let cellElements;
    let hoverState = {
        element: null,
        startTime: null,
        progress: 0
    };

    // Gaze tracking state
    const SENSITIVITY = 6;
    const SMOOTHING = 0.15;
    let prevX = 0, prevY = 0;

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
            // No click listener, we use dwell
            boardElement.appendChild(cell);
            cellElements.push(cell);
        }
    };

    const handleAction = (element) => {
        if (element.classList.contains('cell')) {
            if (element.classList.contains(X_CLASS) || element.classList.contains(CIRCLE_CLASS)) return;
            const currentClass = circleTurn ? CIRCLE_CLASS : X_CLASS;
            placeMark(element, currentClass);
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
        } else if (element.classList.contains('level-btn')) {
            startGame(element.dataset.level);
        } else if (element.id === 'newGameButton') {
            startGame(currentLevel);
        } else if (element.id === 'exitButton') {
            resetGame();
        } else if (element.id === 'closeButton') {
            exitApp();
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
        return cellElements.every(cell => {
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
        const availableCells = cellElements.filter(
            cell => !cell.classList.contains(X_CLASS) && !cell.classList.contains(CIRCLE_CLASS)
        );

        let moveCell;
        if (currentLevel === 'easy') {
            moveCell = availableCells[Math.floor(Math.random() * availableCells.length)];
        } else {
            const bestMoveIndex = findBestMove();
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

    function exitApp() {
        if (videoElement && videoElement.srcObject) {
            const stream = videoElement.srcObject;
            const tracks = stream.getTracks();
            tracks.forEach(track => track.stop());
        }
        document.body.innerHTML = `
            <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; background:linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); color:white; font-family:sans-serif; text-align:center; position:fixed; top:0; left:0; width:100%; z-index:10000;">
                <h1 style="font-size:3rem; margin-bottom:10px;">Session Ended</h1>
                <p style="font-size:1.5rem; opacity:0.8; margin-bottom:10px;">The eye tracker has been turned off.</p>
                <p style="margin-bottom:30px;">You can now safely close this tab.</p>
                <button onclick="location.reload()" style="padding:15px 30px; cursor:pointer; background:rgba(255,255,255,0.2); color:white; border:1px solid white; border-radius:10px; font-size:1.1rem;">Restart Application</button>
            </div>
        `;
    }

    // MediaPipe Setup
    const faceMesh = new FaceMesh({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
    });

    faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    faceMesh.onResults(onResults);

    function onResults(results) {
        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            const landmarks = results.multiFaceLandmarks[0];
            const leftIris = [468, 469, 470, 471];
            const rightIris = [473, 474, 475, 476];
            
            const getCenter = (indices) => {
                let x = 0, y = 0;
                indices.forEach(i => {
                    x += landmarks[i].x;
                    y += landmarks[i].y;
                });
                return { x: x / indices.length, y: y / indices.length };
            };
            
            const lc = getCenter(leftIris);
            const rc = getCenter(rightIris);
            const avgX = (lc.x + rc.x) / 2;
            const avgY = (lc.y + rc.y) / 2;
            
            // Invert X (0.5 - ...) to handle the webcam mirroring
            let targetX = (0.5 - (avgX - 0.5) * SENSITIVITY) * window.innerWidth;
            let targetY = (0.5 + (avgY - 0.5) * SENSITIVITY) * window.innerHeight;
            
            prevX = SMOOTHING * targetX + (1 - SMOOTHING) * prevX;
            prevY = SMOOTHING * targetY + (1 - SMOOTHING) * prevY;
            
            updateGazePointer(prevX, prevY);
        } else {
            gazePointer.style.display = 'none';
        }
    }

    function updateGazePointer(x, y) {
        gazePointer.style.left = `${x}px`;
        gazePointer.style.top = `${y}px`;
        gazePointer.style.display = 'block';

        const element = document.elementFromPoint(x, y);
        const target = element?.closest('.cell, .level-btn, #newGameButton, #exitButton, #closeButton');

        if (target) {
            if (hoverState.element === target) {
                const elapsed = Date.now() - hoverState.startTime;
                hoverState.progress = Math.min(elapsed / DWELL_DURATION, 1);
                target.style.setProperty('--dwell-progress', `${hoverState.progress * 100}%`);

                if (hoverState.progress === 1) {
                    handleAction(target);
                    hoverState.element = null;
                    target.style.setProperty('--dwell-progress', '0%');
                }
            } else {
                if (hoverState.element) {
                    hoverState.element.style.setProperty('--dwell-progress', '0%');
                }
                hoverState.element = target;
                hoverState.startTime = Date.now();
                hoverState.progress = 0;
            }
        } else {
            if (hoverState.element) {
                hoverState.element.style.setProperty('--dwell-progress', '0%');
                hoverState.element = null;
            }
        }
    }

    const camera = new Camera(videoElement, {
        onFrame: async () => {
            await faceMesh.send({ image: videoElement });
        },
        width: 640,
        height: 480
    });

    camera.start().catch(err => {
        console.error("Camera access denied:", err);
    });
});
