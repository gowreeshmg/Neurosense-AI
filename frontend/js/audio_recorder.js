/* ==========================================================================
   NeuroSense AI — Audio Recorder & Live Waveform Visualizer
   ========================================================================== */

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let audioBlob = null;
let recordingInterval = null;
let recordingSeconds = 0;
let audioContext = null;
let analyserNode = null;
let animationFrameId = null;
let simulatedAudioVector = null;

/**
 * Toggles microphone audio recording on/off
 */
async function toggleRecording() {
    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
    }
}

/**
 * Starts recording from user microphone using Web Audio API
 */
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        simulatedAudioVector = null;
        
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            console.log("Audio recording finalized. Blob size:", audioBlob.size);
            updateRecordStatus("Recording captured successfully!", "ready");
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        const btnRec = document.getElementById('btnRecord');
        if (btnRec) btnRec.classList.add('recording');
        const iconRec = document.getElementById('recordBtnIcon');
        if (iconRec) iconRec.innerText = '⬛';
        const txtRec = document.getElementById('recordBtnText');
        if (txtRec) txtRec.innerText = 'Stop Voice Recording';
        updateRecordStatus("Recording voice... Speak now", "recording");
        
        // Start timer
        recordingSeconds = 0;
        const timerEl = document.getElementById('recordingTimer');
        if (timerEl) timerEl.innerText = "00:00";
        if (recordingInterval) clearInterval(recordingInterval);
        recordingInterval = setInterval(() => {
            recordingSeconds++;
            const mins = String(Math.floor(recordingSeconds / 60)).padStart(2, '0');
            const secs = String(recordingSeconds % 60).padStart(2, '0');
            const timerEl2 = document.getElementById('recordingTimer');
            if (timerEl2) timerEl2.innerText = `${mins}:${secs}`;
        }, 1000);
        
        // Setup Live Waveform Visualization
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyserNode = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyserNode);
        analyserNode.fftSize = 256;
        
        drawWaveform();
        
    } catch (err) {
        console.error("Microphone access error:", err);
        alert("⚠️ Could not access microphone. Please allow microphone permissions or use the 'Load Sample Stressed Voice' button for instant demo evaluation!");
    }
}

/**
 * Stops live recording
 */
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        
        if (recordingInterval) clearInterval(recordingInterval);
        if (animationFrameId) cancelAnimationFrame(animationFrameId);
        if (audioContext) audioContext.close();
        
        const btnRec = document.getElementById('btnRecord');
        if (btnRec) btnRec.classList.remove('recording');
        const iconRec = document.getElementById('recordBtnIcon');
        if (iconRec) iconRec.innerText = '🔴';
        const txtRec = document.getElementById('recordBtnText');
        if (txtRec) txtRec.innerText = 'Start Voice Recording';
        
        // Draw resting baseline waveform
        drawRestingWaveform();
    }
}

/**
 * Draws dynamic real-time frequency bars on the waveform canvas while recording
 */
function drawWaveform() {
    const canvas = document.getElementById('waveformCanvas');
    if (!canvas || !analyserNode) return;
    const ctx = canvas.getContext('2d');
    
    const bufferLength = analyserNode.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    function renderFrame() {
        if (!isRecording) return;
        animationFrameId = requestAnimationFrame(renderFrame);
        analyserNode.getByteFrequencyData(dataArray);
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const barWidth = (canvas.width / bufferLength) * 2.5;
        let barHeight;
        let x = 0;
        
        for (let i = 0; i < bufferLength; i++) {
            barHeight = (dataArray[i] / 255) * canvas.height * 0.8;
            
            // Cyan to purple gradient for bars
            ctx.fillStyle = `rgb(${barHeight + 50}, 189, 248)`;
            ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            
            x += barWidth + 2;
        }
    }
    renderFrame();
}

/**
 * Draws a calm resting waveform when idle
 */
function drawRestingWaveform() {
    const canvas = document.getElementById('waveformCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, canvas.height / 2);
    
    for (let x = 0; x < canvas.width; x += 10) {
        const y = (canvas.height / 2) + Math.sin(x * 0.05) * 6;
        ctx.lineTo(x, y);
    }
    ctx.stroke();
}

/**
 * Loads a simulated 195-dimensional acoustic feature profile of a stressed student
 */
function loadSampleVoiceProfile() {
    // Generate synthetic acoustic feature vector representing high MFCC tension & elevated spectral energy
    simulatedAudioVector = Array.from({ length: 195 }, (_, i) => {
        if (i < 40) return 0.65 + Math.sin(i) * 0.2; // High MFCC mean
        if (i < 80) return 0.45 + Math.cos(i) * 0.15; // High variance
        return 0.5 + (Math.random() * 0.3);
    });
    
    audioBlob = null; // Clear live blob so analysis uses our high-fidelity simulated vector
    
    updateRecordStatus("Stressed Student Voice Profile Loaded (195 Acoustic Biomarkers Active)", "ready");
    document.getElementById('recordingTimer').innerText = "00:14 (Sample Profile)";
    
    // Draw energetic simulated waveform
    const canvas = document.getElementById('waveformCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = '#f43f5e';
    for (let x = 0; x < canvas.width; x += 12) {
        const h = 20 + Math.random() * 50;
        ctx.fillRect(x, (canvas.height - h) / 2, 8, h);
    }
}

/**
 * Handles uploading an external audio file (.wav, .webm, .mp3, .m4a)
 */
function handleAudioFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    audioBlob = file;
    simulatedAudioVector = null;
    
    const sizeKB = Math.round(file.size / 1024);
    updateRecordStatus(`Uploaded File: ${file.name} (${sizeKB} KB)`, "ready");
    document.getElementById('recordingTimer').innerText = "Uploaded File";
    
    // Draw an energetic visual waveform indicating uploaded file loaded
    const canvas = document.getElementById('waveformCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = '#38bdf8';
    for (let x = 0; x < canvas.width; x += 8) {
        const h = 15 + Math.sin(x * 0.1) * 25 + (Math.random() * 20);
        ctx.fillRect(x, (canvas.height - h) / 2, 5, h);
    }
}

function updateRecordStatus(text, statusClass) {
    const el = document.getElementById('micStatusText');
    if (!el) return;
    el.innerText = text;
    el.className = `status-indicator ${statusClass}`;
}

