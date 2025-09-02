let detector;

async function loadPoseModel() {
    const detectorConfig = {
        modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING
    };
    detector = await poseDetection.createDetector(poseDetection.SupportedModels.MoveNet, detectorConfig);
}

loadPoseModel();

document.addEventListener('DOMContentLoaded', function () {
    // Basic DOM element refs
    const methodBtns = document.querySelectorAll('.method-btn');
    const uploadSection = document.getElementById('upload-section');
    const cameraSection = document.getElementById('camera-section');
    const seeVideosBtn = document.getElementById('see-videos-btn');
    const analyzePoseBtn = document.getElementById('analyze-pose-btn');

    // Handle upload/camera method switching
    methodBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            methodBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            if (this.dataset.method === 'upload') {
                uploadSection.style.display = 'block';
                cameraSection.style.display = 'none';
                stopCamera();
                seeVideosBtn.style.display = 'inline-block';
                analyzePoseBtn.style.display = 'none';
                document.getElementById('live-feedback-container').style.display = 'none';
            } else {
                // Instead of toggling section, redirect to camera page
                window.location.href = '/camera';
            }
        });
    });

    const initialMethodBtn = document.querySelector('.method-btn.active');
    if (initialMethodBtn && initialMethodBtn.dataset.method === 'upload') {
        uploadSection.style.display = 'block';
        cameraSection.style.display = 'none';
        seeVideosBtn.style.display = 'inline-block';
        analyzePoseBtn.style.display = 'none';
        document.getElementById('live-feedback-container').style.display = 'none';
    }

    // File preview logic
    const fileInput = document.getElementById('file');
    const filePreview = document.getElementById('file-preview');
    const previewPlaceholder = document.querySelector('.preview-placeholder');
    const MAX_FILE_SIZE_MB = 50;
    const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

    fileInput.addEventListener('change', function () {
        if (this.files && this.files[0]) {
            const file = this.files[0];
            const fileNameSpan = document.querySelector('.file-upload-text');
            fileNameSpan.textContent = file.name;
            if (file.size > MAX_FILE_SIZE_BYTES) {
                alert(`File size exceeds ${MAX_FILE_SIZE_MB}MB limit. Please choose a smaller file.`);
                this.value = '';
                fileNameSpan.textContent = 'No file chosen';
                return;
            }
            previewPlaceholder.style.display = 'none';
            filePreview.innerHTML = '';
            if (file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                filePreview.appendChild(img);
            } else if (file.type.startsWith('video/')) {
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.controls = true;
                filePreview.appendChild(video);
            }
        }
    });

    // Camera and analysis logic
    const cameraView = document.getElementById('camera-view');
    const cameraCanvas = document.getElementById('camera-canvas');
    const poseCanvas = document.getElementById('pose-canvas');
    const cameraToggleBtn = document.getElementById('start-camera'); // This is now acting as Toggler
    const toggleAnalysisBtn = document.getElementById('toggle-analysis');
    const captureBtn = document.getElementById('capture-btn');
    const cameraData = document.getElementById('camera-data');
    const liveFeedbackElement = document.getElementById('live-feedback');
    const cameraEmoji = document.getElementById('camera-emoji');
    let stream = null;
    let isAnalyzing = false;
    let analysisInterval = null;

    cameraToggleBtn?.addEventListener('click', async function () {
        if (!stream) {
            // Start camera
            try {
                stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                    audio: false
                });
                cameraView.srcObject = stream;

                // Hide emoji
                if (cameraEmoji) cameraEmoji.style.display = 'none';

                // Adjust canvas after metadata loads
                const setCanvasSizes = () => {
                    cameraCanvas.width = cameraView.videoWidth;
                    cameraCanvas.height = cameraView.videoHeight;
                    poseCanvas.width = cameraView.videoWidth;
                    poseCanvas.height = cameraView.videoHeight;
                    poseCanvas.style.width = `${cameraView.clientWidth}px`;
                    poseCanvas.style.height = `${cameraView.clientHeight}px`;
                };
                if (cameraView.videoWidth > 0) setCanvasSizes();
                else cameraView.addEventListener('loadedmetadata', setCanvasSizes, { once: true });

                cameraToggleBtn.textContent = 'Stop Camera';
                toggleAnalysisBtn.disabled = false;
                captureBtn && (captureBtn.disabled = false);
            } catch (err) {
                alert("Could not access the camera. Please check permissions.");
            }
        } else {
            // Stop camera
            stream.getTracks().forEach(track => track.stop());
            cameraView.srcObject = null;
            stream = null;

            // Show emoji placeholder again
            if (cameraEmoji) cameraEmoji.style.display = 'flex';

            cameraToggleBtn.textContent = 'Start Camera';
            toggleAnalysisBtn.disabled = true;
            captureBtn && (captureBtn.disabled = true);
            toggleAnalysisBtn.textContent = 'Start Analysis';
            isAnalyzing = false;
            stopLiveAnalysis();
            // Clean up overlays
            poseCanvas.getContext('2d').clearRect(0, 0, poseCanvas.width, poseCanvas.height);
            if (liveFeedbackElement) liveFeedbackElement.innerHTML = '';
        }
    });

    toggleAnalysisBtn?.addEventListener('click', function () {
        isAnalyzing = !isAnalyzing;
        if (isAnalyzing) {
            this.textContent = 'Stop Analysis';
            startLiveAnalysis();
        } else {
            this.textContent = 'Start Analysis';
            stopLiveAnalysis();
        }
    });

    function startLiveAnalysis() {
        if (analysisInterval) clearInterval(analysisInterval);

        analysisInterval = setInterval(async () => {
            if (!stream || !cameraView.videoWidth || !detector) return;

            const ctx = cameraCanvas.getContext('2d');
            const poseCtx = poseCanvas.getContext('2d');
            cameraCanvas.width = cameraView.videoWidth;
            cameraCanvas.height = cameraView.videoHeight;
            poseCanvas.width = cameraView.videoWidth;
            poseCanvas.height = cameraView.videoHeight;

            ctx.drawImage(cameraView, 0, 0, cameraCanvas.width, cameraCanvas.height);
            poseCtx.clearRect(0, 0, poseCanvas.width, poseCanvas.height);

            const poses = await detector.estimatePoses(cameraView);
            if (poses.length > 0) drawSkeleton(poses[0], poseCtx);
        }, 500);
    }

    function stopLiveAnalysis() {
        if (analysisInterval) {
            clearInterval(analysisInterval);
            analysisInterval = null;
        }
        poseCanvas.getContext('2d').clearRect(0, 0, poseCanvas.width, poseCanvas.height);
        if (liveFeedbackElement) liveFeedbackElement.innerHTML = '';
    }

    function drawSkeleton(pose, ctx) {
        const keypoints = pose.keypoints;
        const adjacentPairs = [
            [0, 1], [1, 3], [0, 2], [2, 4], [5, 7], [7, 9], [6, 8], [8, 10],
            [5, 6], [5, 11], [6, 12], [11, 13], [13, 15], [12, 14], [14, 16]
        ];
        ctx.strokeStyle = 'cyan';
        ctx.lineWidth = 3;
        ctx.beginPath();
        adjacentPairs.forEach(([i, j]) => {
            const kp1 = keypoints[i];
            const kp2 = keypoints[j];
            if (kp1.score > 0.5 && kp2.score > 0.5) {
                ctx.moveTo(kp1.x, kp1.y);
                ctx.lineTo(kp2.x, kp2.y);
            }
        });
        ctx.stroke();
    }

    captureBtn?.addEventListener('click', function () {
        if (!stream) return;
        const ctx = cameraCanvas.getContext('2d');
        cameraCanvas.width = cameraView.videoWidth;
        cameraCanvas.height = cameraView.videoHeight;
        ctx.drawImage(cameraView, 0, 0, cameraCanvas.width, cameraCanvas.height);
        cameraData.value = cameraCanvas.toDataURL('image/jpeg', 0.8);

        previewPlaceholder.style.display = 'none';
        filePreview.innerHTML = '';
        const img = document.createElement('img');
        img.src = cameraCanvas.toDataURL('image/jpeg', 0.8);
        filePreview.appendChild(img);
    });

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            cameraView.srcObject = null;
            cameraToggleBtn.textContent = 'Start Camera';
            if (cameraEmoji) cameraEmoji.style.display = 'flex';
            toggleAnalysisBtn.disabled = true;
            captureBtn && (captureBtn.disabled = true);
            toggleAnalysisBtn.textContent = 'Start Analysis';
            isAnalyzing = false;
        }
        stopLiveAnalysis();
    }

    window.addEventListener('beforeunload', stopCamera);

    // Submission validation, unchanged
    const poseForm = document.getElementById('pose-form');
    const submitBtn = document.getElementById('submit-btn');
    poseForm?.addEventListener('submit', function (e) {
        const poseType = document.getElementById('pose-type').value;
        document.getElementById('pose-type-hidden').value = poseType;

        const method = document.querySelector('.method-btn.active').dataset.method;
        if (method === 'camera') {
            if (!cameraData.value) {
                e.preventDefault();
                alert('Please capture a photo first or start live analysis');
                return false;
            }
        } else {
            if (!fileInput.value) {
                e.preventDefault();
                alert('Please choose a file to upload');
                return false;
            }
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Analyzing...';
        }
    });
});
