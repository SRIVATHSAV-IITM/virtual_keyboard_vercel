const keyboardLayout = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace"],
    ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", "\\"],
    ["CapsLock", "a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "Enter"],
    ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
    ["Space", "Speak", "Save", "Clear"],
    ["Left", "Up", "Down", "Right", "Exit"]
];

const DWELL_DURATION = 800; // 0.8 seconds
let typedText = "";
let fileName = "";
let capsLock = false;
let mode = "edit"; // "edit" or "save"
let hoverState = {
    element: null,
    startTime: null,
    progress: 0
};

// Gaze Tracking State
let lastGazeX = null;
let lastGazeY = null;
const SENSITIVITY = 6;
const SMOOTHING = 0.15;
let prevX = 0, prevY = 0;

const textarea = document.getElementById('main-textarea');
const keyboardContainer = document.getElementById('keyboard-container');
const suggestionBar = document.getElementById('suggestion-bar');
const gazePointer = document.getElementById('gaze-pointer');
const saveOverlay = document.getElementById('save-prompt-overlay');
const filenameInput = document.getElementById('filename-input');
const videoElement = document.getElementById('webcam');
const customCursor = document.getElementById('custom-cursor');

// Mirror element for cursor calculation
const mirror = document.createElement('div');
mirror.id = 'text-mirror';
Object.assign(mirror.style, {
    position: 'absolute',
    visibility: 'hidden',
    whiteSpace: 'pre-wrap',
    wordWrap: 'break-word',
    padding: '0',
    border: 'none',
    left: '-9999px',
    top: '0',
    overflow: 'hidden'
});
document.body.appendChild(mirror);

function updateCursorPosition() {
    if (mode === "save") {
        customCursor.style.display = 'none';
        return;
    }

    // Sync styles from textarea to mirror
    const style = window.getComputedStyle(textarea);
    const properties = ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'padding', 'width', 'boxSizing', 'letterSpacing'];
    properties.forEach(p => mirror.style[p] = style[p]);
    
    // Width must be exact to match wrapping
    mirror.style.width = textarea.clientWidth + 'px';

    // Replace all text and add a zero-width character + marker for position
    mirror.textContent = typedText;
    const marker = document.createElement('span');
    marker.textContent = '\u200B'; // zero-width space
    mirror.appendChild(marker);

    // Calculate position
    const top = marker.offsetTop + 20 - textarea.scrollTop;
    const left = marker.offsetLeft + 20;

    // Show only if within visible textarea bounds
    if (top >= 10 && top < textarea.clientHeight + 20) {
        customCursor.style.top = `${top}px`;
        customCursor.style.left = `${left}px`;
        customCursor.style.display = 'block';
    } else {
        customCursor.style.display = 'none';
    }
}

// Initialize Keyboard
function initKeyboard() {
    keyboardContainer.innerHTML = '';
    keyboardLayout.forEach(row => {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'keyboard-row';
        row.forEach(key => {
            const keyDiv = document.createElement('div');
            keyDiv.className = 'key';
            keyDiv.dataset.key = key;
            
            if (["Space", "Speak", "Save", "Clear"].includes(key)) keyDiv.classList.add('group1');
            if (key === "Enter") keyDiv.classList.add('group2');
            if (key === "Backspace") keyDiv.classList.add('group3');
            if (["Left", "Up", "Down", "Right", "Exit"].includes(key)) keyDiv.classList.add('group4');
            
            if (["Backspace", "Enter", "CapsLock", "Speak", "Clear", "Save", "Left", "Right", "Up", "Down"].includes(key)) {
                keyDiv.classList.add('double');
            }
            if (key === "Space") keyDiv.classList.add('space');
            
            if (/\d/.test(key)) keyDiv.classList.add('number');
            if (/[a-zA-Z]/.test(key) && key.length === 1) keyDiv.classList.add('letter');
            if (key.length === 1 && !/[a-zA-Z0-9]/.test(key)) keyDiv.classList.add('symbol');
            if (key === "CapsLock") keyDiv.classList.add('function');

            const span = document.createElement('span');
            span.textContent = key;
            keyDiv.appendChild(span);
            rowDiv.appendChild(keyDiv);
        });
        keyboardContainer.appendChild(rowDiv);
    });
}

function updateSuggestions() {
    const words_in_text = typedText.trim().split(/\s+/);
    const prefix = words_in_text[words_in_text.length - 1]?.toLowerCase() || "";
    
    if (prefix.length < 2) {
        suggestionBar.innerHTML = '';
        return;
    }
    
    const suggestions = commonWords
        .filter(w => w.startsWith(prefix))
        .slice(0, 5);
        
    renderSuggestions(suggestions);
}

function renderSuggestions(suggestions) {
    suggestionBar.innerHTML = '';
    suggestions.forEach(s => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        div.dataset.suggestion = s;
        const span = document.createElement('span');
        span.textContent = s;
        div.appendChild(span);
        suggestionBar.appendChild(div);
    });
}

function handleKey(key) {
    if (mode === "save") {
        handleSaveKey(key);
        return;
    }

    switch(key) {
        case "Backspace":
            typedText = typedText.slice(0, -1);
            break;
        case "Enter":
            typedText += "\n";
            break;
        case "Space":
            typedText += " ";
            break;
        case "CapsLock":
            capsLock = !capsLock;
            document.querySelectorAll('.key[data-key="CapsLock"]').forEach(k => {
                k.classList.toggle('capslock-active', capsLock);
            });
            document.querySelectorAll('.key.letter span').forEach(span => {
                const k = span.parentElement.dataset.key;
                span.textContent = capsLock ? k.toUpperCase() : k.toLowerCase();
            });
            break;
        case "Speak":
            speak(typedText);
            break;
        case "Clear":
            typedText = "";
            break;
        case "Save":
            mode = "save";
            fileName = "";
            saveOverlay.classList.remove('hidden');
            filenameInput.value = "";
            break;
        case "Exit":
            exitApp();
            break;
        default:
            if (key.length === 1) {
                let char = key;
                if (/[a-z]/.test(key)) {
                    char = capsLock ? key.toUpperCase() : key.toLowerCase();
                }
                typedText += char;
            }
    }
    textarea.value = typedText;
    textarea.scrollTop = textarea.scrollHeight;
    updateCursorPosition();
    updateSuggestions();
}

function handleSaveKey(key) {
    if (key === "Enter") {
        if (fileName) {
            saveToFile(fileName, typedText);
            speak("File saved");
            mode = "edit";
            saveOverlay.classList.add('hidden');
        }
    } else if (key === "Backspace") {
        fileName = fileName.slice(0, -1);
    } else if (key === "Clear") {
        mode = "edit";
        saveOverlay.classList.add('hidden');
    } else if (key.length === 1 || key === "Space") {
        let char = key === "Space" ? " " : key;
        if (/[a-z]/.test(char)) char = capsLock ? char.toUpperCase() : char.toLowerCase();
        fileName += char;
    }
    filenameInput.value = fileName;
}

function speak(text) {
    if (!text) return;
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
}

function saveToFile(name, content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name.endsWith('.txt') ? name : name + '.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

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
        
        // Iris landmark indices (same as Python GazeTracker)
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
        
        // Map normalized coordinates (0-1) to screen with sensitivity
        // We invert X (0.5 - ...) to handle the webcam mirroring
        let targetX = 0.5 - (avgX - 0.5) * SENSITIVITY;
        let targetY = 0.5 + (avgY - 0.5) * SENSITIVITY;
        
        targetX = Math.max(0, Math.min(1, targetX)) * window.innerWidth;
        targetY = Math.max(0, Math.min(1, targetY)) * window.innerHeight;
        
        // Smoothing
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
    const target = element?.closest('.key, .suggestion-item');

    if (target) {
        if (hoverState.element === target) {
            const elapsed = Date.now() - hoverState.startTime;
            hoverState.progress = Math.min(elapsed / DWELL_DURATION, 1);
            target.style.setProperty('--dwell-progress', `${hoverState.progress * 100}%`);

            if (hoverState.progress === 1) {
                if (target.classList.contains('key')) {
                    handleKey(target.dataset.key);
                } else if (target.classList.contains('suggestion-item')) {
                    const words = typedText.trim().split(/\s+/);
                    words[words.length - 1] = target.dataset.suggestion;
                    typedText = words.join(" ") + " ";
                    textarea.value = typedText;
                    updateCursorPosition();
                    updateSuggestions();
                }
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

document.addEventListener('DOMContentLoaded', () => {
    initKeyboard();
    updateCursorPosition();
    camera.start().catch(err => {
        console.error("Camera access denied:", err);
        alert("Please allow camera access for eye tracking.");
    });
});
