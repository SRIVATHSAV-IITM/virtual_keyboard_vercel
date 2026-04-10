const DWELL_DURATION = 1000;
const SENSITIVITY = 6;
const SMOOTHING = 0.15;
const TRIGGER_COOLDOWN = 1000;

let prevX = 0, prevY = 0;
let lastTriggerTime = 0;

let hoverState = {
    element: null,
    startTime: null,
    progress: 0
};

const gazePointer = document.getElementById('gaze-pointer');
const videoElement = document.getElementById('webcam');

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
    const target = Array.from(elements).find(el => el && el.classList && el.classList.contains('interactive'));

    if (target) {
        if (hoverState.element === target) {
            const elapsed = Date.now() - hoverState.startTime;
            hoverState.progress = Math.max(0, Math.min(elapsed / DWELL_DURATION, 1));
            target.style.setProperty('--dwell-progress', `${hoverState.progress * 100}%`);

            if (hoverState.progress === 1) {
                let action = target.dataset.action;
                let url = target.dataset.url;
                resetHover();
                lastTriggerTime = Date.now();
                
                if (action === "launch") {
                    window.location.href = url;
                } else if (action === "exit") {
                    exitSuite();
                }
                
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

function exitSuite() {
    if (videoElement && videoElement.srcObject) {
        const stream = videoElement.srcObject;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
    }
    document.body.innerHTML = `
        <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; background:#1e3c72; color:white; font-family:sans-serif; text-align:center;">
            <h1>Suite Closed</h1>
            <p>Eye tracking has been disabled.</p>
            <button onclick="location.reload()" style="margin-top:20px; padding:10px 20px;">Restart</button>
        </div>
    `;
}

const camera = new Camera(videoElement, {
    onFrame: async () => {
        await faceMesh.send({ image: videoElement });
    },
    width: 640,
    height: 480
});

document.addEventListener('DOMContentLoaded', () => {
    camera.start().catch(err => console.error(err));
});
