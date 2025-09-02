let detector = null;
let stream = null;
let intervalId = null;
let isAnalyzing = false;
let showSkeleton = false;

const emojiEl = document.getElementById('camera-emoji');

async function loadModel() {
  detector = await poseDetection.createDetector(
    poseDetection.SupportedModels.MoveNet,
    { modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING }
  );
}

async function fetchBackendFeedback(frameData) {
  try {
    const res = await fetch('/predict_live_frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frame: frameData })
    });

    const data = await res.json();
    console.log('✅ Feedback from backend:', data);

    const label = data.label || 'Unknown';
    const confidence = data.confidence !== undefined ? `${data.confidence.toFixed(1)}%` : 'N/A';
    const correctness = data.correctness || (data.confidence < 50 ? 'Low confidence in prediction' : 'High confidence');

    let feedbackItems = [];

    if (Array.isArray(data.feedback)) {
      feedbackItems = data.feedback;
    } else if (typeof data.feedback === 'string') {
      feedbackItems = [data.feedback];
    } else if (typeof data.feedback === 'object' && data.feedback !== null) {
      feedbackItems = Object.values(data.feedback);
    }

    return [
      ...feedbackItems.map(item => `- ${item}`)
    ];
  } catch (err) {
    console.error('Error fetching feedback:', err);
    return ['Error retrieving feedback'];
  }
}

function drawSkeleton(pose, ctx) {
  const adjacentPairs = [
    [0, 1], [1, 3], [0, 2], [2, 4],
    [5, 7], [7, 9], [6, 8], [8, 10],
    [5, 6], [5, 11], [6, 12],
    [11, 13], [13, 15], [12, 14], [14, 16]
  ];

  ctx.strokeStyle = 'cyan';
  ctx.lineWidth = 3;
  ctx.beginPath();
  adjacentPairs.forEach(([i, j]) => {
    const kp1 = pose.keypoints[i];
    const kp2 = pose.keypoints[j];
    if (kp1.score > 0.5 && kp2.score > 0.5) {
      ctx.moveTo(kp1.x, kp1.y);
      ctx.lineTo(kp2.x, kp2.y);
    }
  });
  ctx.stroke();
}

function showFeedbackList(list) {
  const feedbackEl = document.getElementById('live-feedback'); // FIXED
  if (!feedbackEl) return;

  feedbackEl.innerHTML = '';
  list.forEach(text => {
    const li = document.createElement('li');
    li.textContent = text;
    feedbackEl.appendChild(li);
  });
}


function startAnalysis(video, canvas) {
  const container = document.getElementById('live-feedback-container');
  if (container) container.style.display = 'block';

  intervalId = setInterval(async () => {
    if (!detector || !video.videoWidth) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const poses = await detector.estimatePoses(video);

    if (poses.length > 0) {
      if (showSkeleton) drawSkeleton(poses[0], ctx);

      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = video.videoWidth;
      tempCanvas.height = video.videoHeight;
      const tempCtx = tempCanvas.getContext('2d');
      tempCtx.drawImage(video, 0, 0);
      const frameData = tempCanvas.toDataURL('image/jpeg', 0.8);

      const feedback = await fetchBackendFeedback(frameData);
      showFeedbackList(feedback);
    } else {
      showFeedbackList(['❌ No pose detected']);
    }
  }, 500);
}

function stopAnalysis(canvas) {
  if (intervalId !== null) {
    clearInterval(intervalId);
    intervalId = null;
  }

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  showFeedbackList([]);

  const container = document.getElementById('live-feedback-container');
  if (container) container.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', async () => {
  await loadModel();

  const video = document.getElementById('camera-view');
  const canvas = document.getElementById('pose-canvas');
  const startBtn = document.getElementById('start-camera');
  const toggleBtn = document.getElementById('toggle-analysis');

  document.getElementById('mode-live').addEventListener('click', () => {
    showSkeleton = false;
    document.getElementById('mode-live').classList.add('active');
    document.getElementById('mode-skeleton').classList.remove('active');
  });

  document.getElementById('mode-skeleton').addEventListener('click', () => {
    showSkeleton = true;
    document.getElementById('mode-skeleton').classList.add('active');
    document.getElementById('mode-live').classList.remove('active');
  });

  startBtn.addEventListener('click', async () => {
    if (!stream) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: 640, height: 480 },
          audio: false
        });
        video.srcObject = stream;
        video.onloadedmetadata = () => {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          canvas.style.width = video.clientWidth + 'px';
          canvas.style.height = video.clientHeight + 'px';
        };
        if (emojiEl) emojiEl.style.display = 'none';
        startBtn.textContent = 'Stop Camera';
        toggleBtn.disabled = false;
      } catch (err) {
        alert('Camera access denied or not available.');
        console.error(err);
      }
    } else {
      stream.getTracks().forEach(track => track.stop());
      video.srcObject = null;
      stream = null;
      if (emojiEl) emojiEl.style.display = 'flex';
      startBtn.textContent = 'Start Camera';
      toggleBtn.disabled = true;

      if (isAnalyzing) {
        isAnalyzing = false;
        toggleBtn.innerText = 'Start Analysis';
        stopAnalysis(canvas);
      }
    }
  });

 toggleBtn.addEventListener('click', () => {
  if (!isAnalyzing) {
    isAnalyzing = true;
    toggleBtn.innerText = 'Stop Analysis';
    startAnalysis(video, canvas);
  } else {
    isAnalyzing = false;
    toggleBtn.innerText = 'Start Analysis';
    stopAnalysis(canvas);
  }
});


  window.addEventListener('beforeunload', () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    if (isAnalyzing) {
      stopAnalysis(document.getElementById('pose-canvas'));
    }
  });
});
