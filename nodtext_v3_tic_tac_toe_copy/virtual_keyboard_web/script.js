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

const textarea = document.getElementById('main-textarea');
const keyboardContainer = document.getElementById('keyboard-container');
const suggestionBar = document.getElementById('suggestion-bar');
const gazePointer = document.getElementById('gaze-pointer');
const saveOverlay = document.getElementById('save-prompt-overlay');
const filenameInput = document.getElementById('filename-input');

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
            
            // Add group classes and multipliers
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
            if (key.length > 1 && !["Space", "Speak", "Save", "Clear", "Enter", "Backspace", "Left", "Up", "Down", "Right", "Exit", "CapsLock"].includes(key)) {
                 keyDiv.classList.add('function');
            }
            if (key === "CapsLock") keyDiv.classList.add('function');

            const span = document.createElement('span');
            span.textContent = key;
            keyDiv.appendChild(span);
            rowDiv.appendChild(keyDiv);
        });
        keyboardContainer.appendChild(rowDiv);
    });
}

async function updateSuggestions() {
    // Call python NLTK suggestions
    const suggestions = await eel.get_suggestions(typedText)();
    renderSuggestions(suggestions);
}

function renderSuggestions(suggestions) {
    suggestionBar.innerHTML = '';
    if (!suggestions || suggestions.length === 0) return;
    
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
            // Update letter keys display
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
            eel.close_keyboard()(() => {
                window.close();
            });
            break;
        case "Left":
        case "Up":
        case "Down":
        case "Right":
            // Navigation can be implemented if needed
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
    updateSuggestions();
}

function handleSaveKey(key) {
    if (key === "Enter") {
        if (fileName) {
            eel.save_file(fileName, typedText)((response) => {
                speak("File saved");
                mode = "edit";
                saveOverlay.classList.add('hidden');
            });
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
    // Call python TTS (pyttsx3) to match original behavior
    eel.speak_text(text)();
}

async function updateGaze() {
    const coords = await eel.get_gaze_coordinates()();
    const x = coords[0];
    const y = coords[1];

    if (x !== null && y !== null) {
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
                        // Handle suggestion replacement
                        const words = typedText.trim().split(/\s+/);
                        words[words.length - 1] = target.dataset.suggestion;
                        typedText = words.join(" ") + " ";
                        textarea.value = typedText;
                        updateSuggestions();
                    }
                    // Reset hover after trigger
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
    } else {
        gazePointer.style.display = 'none';
    }

    requestAnimationFrame(updateGaze);
}

document.addEventListener('DOMContentLoaded', () => {
    initKeyboard();
    updateGaze();
});
