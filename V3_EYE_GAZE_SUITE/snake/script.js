const DWELL_DURATION = 1000; // ms
const SENSITIVITY = 6;
const SMOOTHING = 0.15;
const TRIGGER_COOLDOWN = 1000;

// Game constants
const CELL_SIZE = 25;
const NUMBER_OF_CELLS = 25;
const GAME_SIZE = CELL_SIZE * NUMBER_OF_CELLS;

// Colors from original
const GREEN = "#adc860";
const DARK_GREEN = "#2b3318";
const WHITE = "#ffffff";

let prevX = 0, prevY = 0;
let lastTriggerTime = 0;

let hoverState = {
    element: null,
    startTime: null,
    progress: 0
};

// Game State
let gameState = "MENU"; // MENU, PLAYING, GAME_OVER
let score = 0;
let snake = [];
let direction = { x: 1, y: 0 };
let food = { x: 15, y: 15 };
let gameInterval = null;
let currentSpeed = 200;

const DIFFICULTY_LEVELS = {
    "Easy": 300,
    "Medium": 200,
    "Hard": 100,
    "Extreme": 50
};

// Assets
const foodImage = new Image();
foodImage.src = 'Graphics/food.png';
const eatSound = new Audio('Sounds/eat.mp3');
const wallSound = new Audio('Sounds/wall.mp3');

// DOM Elements
const appContainer = document.getElementById('game-container');
const uiLayer = document.getElementById('ui-layer');
const gazePointer = document.getElementById('gaze-pointer');
const videoElement = document.getElementById('webcam');
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');

canvas.width = GAME_SIZE;
canvas.height = GAME_SIZE;

function initApp() {
    renderMenu();
}

function renderMenu() {
    gameState = "MENU";
    uiLayer.innerHTML = `
        <div class="screen" id="menu-screen">
            <div class="title">Retro Snake</div>
            <div class="difficulty-label">Select Difficulty</div>
            <div class="button-container">
                <div class="interactive" data-action="set_difficulty" data-value="Easy">Easy</div>
                <div class="interactive" data-action="set_difficulty" data-value="Medium">Medium</div>
                <div class="interactive" data-action="set_difficulty" data-value="Hard">Hard</div>
                <div class="interactive" data-action="set_difficulty" data-value="Extreme">Extreme</div>
            </div>
            <div style="display:flex; flex-direction:column; gap:20px; margin-top:40px; align-items:center;">
                <div class="interactive" data-action="start_game"><span>Start Game</span></div>
                <div style="display:flex; gap:20px;">
                    <div class="interactive" data-action="launcher" style="background:#555;"><span>Back to Launcher</span></div>
                    <div class="interactive" data-action="exit" style="background:#ff4c4c;"><span>Exit Game</span></div>
                </div>
            </div>
        </div>
    `;
    resetGame();
    draw();
}

function renderGameOver() {
    gameState = "GAME_OVER";
    uiLayer.innerHTML = `
        <div class="screen" id="gameover-screen">
            <div class="title" style="color: #ff4c4c;">GAME OVER</div>
            <div style="font-size: 2rem; margin-bottom: 20px;">Score: ${score}</div>
            <div class="button-container">
                <div class="interactive" data-action="start_game">Restart</div>
                <div class="interactive" data-action="menu">Main Menu</div>
            </div>
        </div>
    `;
}

function resetGame() {
    snake = [
        { x: 6, y: 9 },
        { x: 5, y: 9 },
        { x: 4, y: 9 }
    ];
    direction = { x: 1, y: 0 };
    score = 0;
    generateFood();
}

function generateFood() {
    food = {
        x: Math.floor(Math.random() * NUMBER_OF_CELLS),
        y: Math.floor(Math.random() * NUMBER_OF_CELLS)
    };
    // Check if food is on snake
    for (let segment of snake) {
        if (segment.x === food.x && segment.y === food.y) {
            generateFood();
            break;
        }
    }
}

function startGame() {
    gameState = "PLAYING";
    uiLayer.innerHTML = `
        <div class="score">Score: 0</div>
        <div id="grid-overlay" style="width: ${GAME_SIZE}px; height: ${GAME_SIZE}px;">
            <div class="grid-cell"></div>
            <div class="grid-cell"><span class="arrow">↑</span></div>
            <div class="grid-cell"></div>
            <div class="grid-cell"><span class="arrow">←</span></div>
            <div class="grid-cell"></div>
            <div class="grid-cell"><span class="arrow">→</span></div>
            <div class="grid-cell"></div>
            <div class="grid-cell"><span class="arrow">↓</span></div>
            <div class="grid-cell"></div>
        </div>
        <div style="position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); pointer-events: auto;">
             <div class="interactive" data-action="menu" style="padding: 10px 20px; font-size: 1rem;">Exit to Menu</div>
        </div>
    `;
    resetGame();
    if (gameInterval) clearInterval(gameInterval);
    gameInterval = setInterval(update, currentSpeed);
}

function update() {
    if (gameState !== "PLAYING") return;

    const head = { x: snake[0].x + direction.x, y: snake[0].y + direction.y };

    // Collision with walls
    if (head.x < 0 || head.x >= NUMBER_OF_CELLS || head.y < 0 || head.y >= NUMBER_OF_CELLS) {
        gameOver();
        return;
    }

    // Collision with self
    for (let segment of snake) {
        if (head.x === segment.x && head.y === segment.y) {
            gameOver();
            return;
        }
    }

    snake.unshift(head);

    // Eating food
    if (head.x === food.x && head.y === food.y) {
        score++;
        document.querySelector('.score').innerText = `Score: ${score}`;
        eatSound.play();
        generateFood();
    } else {
        snake.pop();
    }

    draw();
}

function gameOver() {
    gameState = "GAME_OVER";
    clearInterval(gameInterval);
    wallSound.play();
    renderGameOver();
}

function draw() {
    ctx.fillStyle = GREEN;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw snake
    ctx.fillStyle = DARK_GREEN;
    ctx.strokeStyle = WHITE;
    ctx.lineWidth = 1;
    for (let segment of snake) {
        ctx.fillRect(segment.x * CELL_SIZE, segment.y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
        ctx.strokeRect(segment.x * CELL_SIZE, segment.y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    }

    // Draw food
    if (foodImage.complete) {
        ctx.drawImage(foodImage, food.x * CELL_SIZE, food.y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    } else {
        ctx.fillStyle = "red";
        ctx.fillRect(food.x * CELL_SIZE, food.y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    }
}

function handleAction(action, value) {
    if (action === "set_difficulty") {
        currentSpeed = DIFFICULTY_LEVELS[value];
        // Visual feedback for selection
        document.querySelectorAll('[data-action="set_difficulty"]').forEach(btn => {
            btn.style.borderColor = "#2b3318";
            btn.style.background = "#3cb371";
        });
        const activeBtn = Array.from(document.querySelectorAll('[data-action="set_difficulty"]')).find(btn => btn.innerText === value);
        if (activeBtn) {
            activeBtn.style.borderColor = "white";
            activeBtn.style.background = "#50c878";
        }
    } else if (action === "start_game") {
        startGame();
    } else if (action === "menu") {
        clearInterval(gameInterval);
        renderMenu();
    } else if (action === "exit") {
        exitApp();
    } else if (action === "launcher") {
        window.location.href = "../index.html";
    }
}

function exitApp() {
    if (videoElement && videoElement.srcObject) {
        const stream = videoElement.srcObject;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
    }
    document.body.innerHTML = `
        <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; background:linear-gradient(135deg, #2b3318 0%, #adc860 100%); color:white; font-family:sans-serif; text-align:center; position:fixed; top:0; left:0; width:100%; z-index:10000;">
            <h1 style="font-size:3rem; margin-bottom:10px;">Session Ended</h1>
            <p style="font-size:1.5rem; opacity:0.8; margin-bottom:10px;">The eye tracker has been turned off.</p>
            <div style="display:flex; gap:20px; margin-top:30px;">
                <button onclick="location.href='../index.html'" style="padding:15px 30px; cursor:pointer; background:rgba(255,255,255,0.2); color:white; border:1px solid white; border-radius:10px; font-size:1.1rem;">Back to Launcher</button>
                <button onclick="location.reload()" style="padding:15px 30px; cursor:pointer; background:rgba(255,255,255,0.2); color:white; border:1px solid white; border-radius:10px; font-size:1.1rem;">Restart Snake</button>
            </div>
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
        
        let targetX = 0.5 - (avgX - 0.5) * SENSITIVITY;
        let targetY = 0.5 + (avgY - 0.5) * SENSITIVITY;
        
        targetX = Math.max(0, Math.min(1, targetX)) * window.innerWidth;
        targetY = Math.max(0, Math.min(1, targetY)) * window.innerHeight;
        
        prevX = SMOOTHING * targetX + (1 - SMOOTHING) * prevX;
        prevY = SMOOTHING * targetY + (1 - SMOOTHING) * prevY;
        
        updateGazePointer(prevX, prevY);
    } else {
        gazePointer.style.display = 'none';
        resetHover();
    }
}

function resetHover() {
    if (hoverState.element) {
        hoverState.element.style.setProperty('--dwell-progress', '0%');
        hoverState.element = null;
    }
}

function updateGazePointer(x, y) {
    gazePointer.style.left = `${x}px`;
    gazePointer.style.top = `${y}px`;
    gazePointer.style.display = 'block';

    if (Date.now() - lastTriggerTime < TRIGGER_COOLDOWN) {
        resetHover();
        return;
    }

    // Gaze-to-Direction logic for PLAYING state
    if (gameState === "PLAYING") {
        const canvasRect = canvas.getBoundingClientRect();
        if (x >= canvasRect.left && x <= canvasRect.right && y >= canvasRect.top && y <= canvasRect.bottom) {
            const relX = (x - canvasRect.left) / canvasRect.width;
            const relY = (y - canvasRect.top) / canvasRect.height;

            const col = Math.floor(relX * 3);
            const row = Math.floor(relY * 3);

            // Update UI feedback for grid
            const cells = document.querySelectorAll('.grid-cell');
            cells.forEach(c => c.classList.remove('active-cell'));
            const cellIndex = row * 3 + col;
            if (cells[cellIndex]) cells[cellIndex].classList.add('active-cell');

            if (row === 0 && col === 1) { // Up
                if (direction.y !== 1) direction = { x: 0, y: -1 };
            } else if (row === 2 && col === 1) { // Down
                if (direction.y !== -1) direction = { x: 0, y: 1 };
            } else if (row === 1 && col === 0) { // Left
                if (direction.x !== 1) direction = { x: -1, y: 0 };
            } else if (row === 1 && col === 2) { // Right
                if (direction.x !== -1) direction = { x: 1, y: 0 };
            }
        }
    }

    // Dwell logic for buttons
    const elements = document.elementsFromPoint(x, y);
    const target = Array.from(elements).find(el => el && el.classList && el.classList.contains('interactive'));

    if (target) {
        if (hoverState.element === target) {
            const elapsed = Date.now() - hoverState.startTime;
            hoverState.progress = Math.max(0, Math.min(elapsed / DWELL_DURATION, 1));
            target.style.setProperty('--dwell-progress', `${hoverState.progress * 100}%`);

            if (hoverState.progress === 1) {
                let action = target.dataset.action;
                let value = target.dataset.value;
                resetHover();
                lastTriggerTime = Date.now();
                handleAction(action, value);
                // Fake stay to prevent immediate re-trigger
                hoverState.element = target;
                hoverState.startTime = Date.now() + 100000;
            }
        } else {
            resetHover();
            hoverState.element = target;
            hoverState.startTime = Date.now();
            hoverState.progress = 0;
        }
    } else {
        resetHover();
    }
}

const camera = new Camera(videoElement, {
    onFrame: async () => {
        await faceMesh.send({ image: videoElement });
    },
    width: 640,
    height: 480
});

document.addEventListener('DOMContentLoaded', () => {
    initApp();
    camera.start().catch(err => {
        console.error("Camera access denied:", err);
        alert("Please allow camera access for eye tracking.");
    });
});
