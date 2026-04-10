const DWELL_DURATION = 800; // ms
const SENSITIVITY = 6;
const SMOOTHING = 0.15;
const TRIGGER_COOLDOWN = 1000; // ms - ignore dwell for 1s after a trigger

let prevX = 0, prevY = 0;
let lastTriggerTime = 0;

let hoverState = {
    element: null,
    startTime: null,
    progress: 0
};

// Game State
let currentState = "welcome"; // welcome, level_select, gameplay
let currentLevel = 0;
const levels = [
    ["My", "name", "is", "Priya"],
    ["I", "always", "try", "my", "best", "level"],
    ["Learning", "new", "things", "makes", "me", "stronger", "and", "happier", "!"]
];
let targetSentence = [];
let selectedWords = [];
let remainingWords = [];

// DOM Elements
const appContainer = document.getElementById('app-container');
const gazePointer = document.getElementById('gaze-pointer');
const videoElement = document.getElementById('webcam');

// Quotes
const ENCOURAGEMENT_QUOTES = [
    "You're doing great!",
    "Keep it up!",
    "Awesome job!",
    "Believe in yourself!",
    "Every step is progress."
];

function initApp() {
    renderWelcome();
}

function renderWelcome() {
    currentState = "welcome";
    const quote = ENCOURAGEMENT_QUOTES[Math.floor(Math.random() * ENCOURAGEMENT_QUOTES.length)];
    appContainer.innerHTML = `
        <div class="screen" id="welcome-screen">
            <div class="title">Welcome to Space Confidence!</div>
            <div class="quote">${quote}</div>
            <div style="display:flex; flex-direction:column; gap:20px; margin-top:50px; align-items:center;">
                <div class="interactive btn" data-action="start"><span>Start</span></div>
                <div style="display:flex; gap:20px;">
                    <div class="interactive btn" data-action="launcher" style="background:#555; color:white;"><span>Back to Launcher</span></div>
                    <div class="interactive btn" data-action="exit" style="background:#ff4c4c; color:white;"><span>Exit Game</span></div>
                </div>
            </div>
        </div>
    `;
}

function renderLevelSelect() {
    currentState = "level_select";
    appContainer.innerHTML = `
        <div class="screen" id="level-select-screen">
            <div class="title">Select Level</div>
            <div class="level-grid">
                <div class="interactive level-btn" style="background:#ffb6c1" data-action="level_0"><span>Level 1<br>(4 words)</span></div>
                <div class="interactive level-btn" style="background:#87ceeb" data-action="level_1"><span>Level 2<br>(6 words)</span></div>
                <div class="interactive level-btn" style="background:#98fb98" data-action="level_2"><span>Level 3<br>(9 words)</span></div>
            </div>
            <div style="margin-top:50px;">
                <div class="interactive btn" data-action="back_welcome"><span>Back</span></div>
            </div>
        </div>
    `;
}

function renderGameplay(levelIndex) {
    currentState = "gameplay";
    currentLevel = levelIndex;
    targetSentence = levels[levelIndex];
    selectedWords = [];
    remainingWords = [...targetSentence];
    remainingWords.sort(() => Math.random() - 0.5); // shuffle

    updateGameplayUI();
}

const baseColors = [
    "#87ceeb", "#90ee90", "#ffb6c1",
    "#fffacd", "#ffa07a", "#dda0dd",
    "#ffdab9", "#f0e68c", "#98fb98"
];

function updateGameplayUI(showFeedback = false, feedbackCorrect = false) {
    let wordBoxesHTML = remainingWords.map((word, i) => {
        let color = baseColors[i % baseColors.length];
        return `<div class="interactive word-box" data-action="select_word" data-word="${word}" style="background-color:${color}"><span>${word}</span></div>`;
    }).join('');

    let overlayHTML = '';
    if (showFeedback) {
        let msg = feedbackCorrect ? ENCOURAGEMENT_QUOTES[Math.floor(Math.random() * ENCOURAGEMENT_QUOTES.length)] : "Try Again! You're learning every time.";
        let btnText = feedbackCorrect ? "Next Round" : "Try Again";
        let btnAction = feedbackCorrect ? "next_round" : "try_again_feedback";
        let cls = feedbackCorrect ? "correct" : "wrong";
        
        overlayHTML = `
            <div class="overlay" id="feedback-overlay">
                <div class="overlay-content ${cls}">
                    <div class="overlay-msg">${msg}</div>
                    <div class="interactive btn" data-action="${btnAction}"><span>${btnText}</span></div>
                </div>
            </div>
        `;
    }

    appContainer.innerHTML = `
        <div class="screen" id="gameplay-screen">
            <div class="top-bar target-bar">Target: ${targetSentence.join(" ")}</div>
            <div class="top-bar current-bar">Current: ${selectedWords.join(" ")}</div>
            
            <div class="word-area" id="word-area">
                ${wordBoxesHTML}
            </div>

            <div class="control-area">
                <div class="interactive control-btn" data-action="backspace"><span>Backspace</span></div>
                <div class="interactive control-btn" data-action="try_again"><span>Try Again</span></div>
                <div class="interactive control-btn" data-action="next"><span>Next</span></div>
                <div class="interactive control-btn" data-action="exit_gameplay"><span>Exit</span></div>
            </div>
            
            ${overlayHTML}
        </div>
    `;
}

function handleAction(action, element) {
    if (action === "start") renderLevelSelect();
    else if (action === "exit") exitApp();
    else if (action === "launcher") window.location.href = "../index.html";
    else if (action === "back_welcome") renderWelcome();
    else if (action.startsWith("level_")) {
        let lvl = parseInt(action.split("_")[1]);
        renderGameplay(lvl);
    }
    else if (action === "exit_gameplay") renderWelcome();
    else if (action === "next") {
        renderGameplay((currentLevel + 1) % levels.length);
    }
    else if (action === "try_again") {
        renderGameplay(currentLevel);
    }
    else if (action === "backspace") {
        if (selectedWords.length > 0) {
            let lastWord = selectedWords.pop();
            remainingWords.push(lastWord);
            updateGameplayUI();
        }
    }
    else if (action === "select_word") {
        let word = element.dataset.word;
        let expectedWord = targetSentence[selectedWords.length];
        
        if (expectedWord && word.trim() === expectedWord.trim()) {
            selectedWords.push(word);
            let idx = remainingWords.indexOf(word);
            if (idx > -1) remainingWords.splice(idx, 1);
            
            if (selectedWords.length === targetSentence.length) {
                updateGameplayUI(true, true);
            } else {
                updateGameplayUI();
            }
        } else {
            element.classList.add("error");
            setTimeout(() => {
                if (document.body.contains(element)) {
                    element.classList.remove("error");
                }
            }, 500);
        }
    }
    else if (action === "next_round") {
        renderGameplay((currentLevel + 1) % levels.length);
    }
    else if (action === "try_again_feedback") {
        renderGameplay(currentLevel);
    }
}

function exitApp() {
    if (videoElement && videoElement.srcObject) {
        const stream = videoElement.srcObject;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
    }
    document.body.innerHTML = `
        <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; background:linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color:white; font-family:sans-serif; text-align:center; position:fixed; top:0; left:0; width:100%; z-index:10000;">
            <h1 style="font-size:3rem; margin-bottom:10px;">Session Ended</h1>
            <p style="font-size:1.5rem; opacity:0.8; margin-bottom:10px;">The eye tracker has been turned off.</p>
            <div style="display:flex; gap:20px; margin-top:30px;">
                <button onclick="location.href='../index.html'" style="padding:15px 30px; cursor:pointer; background:rgba(255,255,255,0.2); color:white; border:1px solid white; border-radius:10px; font-size:1.1rem;">Back to Launcher</button>
                <button onclick="location.reload()" style="padding:15px 30px; cursor:pointer; background:rgba(255,255,255,0.2); color:white; border:1px solid white; border-radius:10px; font-size:1.1rem;">Restart Game</button>
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

    const elements = document.elementsFromPoint(x, y);
    if (!elements) {
        resetHover();
        return;
    }

    const target = Array.from(elements).find(el => el && el.classList && el.classList.contains('interactive'));

    if (target && !target.classList.contains('error')) {
        if (hoverState.element === target) {
            const elapsed = Date.now() - hoverState.startTime;
            hoverState.progress = Math.max(0, Math.min(elapsed / DWELL_DURATION, 1));
            target.style.setProperty('--dwell-progress', `${hoverState.progress * 100}%`);

            if (hoverState.progress === 1) {
                let action = target.dataset.action;
                let currentTarget = target;
                resetHover();
                lastTriggerTime = Date.now();
                handleAction(action, currentTarget);
                // Force user to look away before next interaction
                hoverState.element = currentTarget;
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