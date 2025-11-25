const videoEl = document.getElementById("video");
let autoplayResolved = false;

let ws;
let pc;

async function startWebRTC() {
  pc = new RTCPeerConnection();

  videoEl.muted = true;
  videoEl.autoplay = true;
  videoEl.playsInline = true;

  pc.ontrack = (event) => {
    const [stream] = event.streams;
    videoEl.srcObject = stream;
    const safePlay = async () => {
      try {
        await videoEl.play();
        autoplayResolved = true;
      } catch (err) {
        console.warn("video.play() blocked, waiting for user interaction", err);
      }
    };
    safePlay();
  };

  pc.oniceconnectionstatechange = () => {
    // Monitor connection state silently
  };

  pc.onconnectionstatechange = () => {
    // Monitor connection state silently
  };

  pc.addTransceiver("video", { direction: "recvonly" });

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  const resp = await fetch("/webrtc/offer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sdp: pc.localDescription.sdp,
      type: pc.localDescription.type,
    }),
  });

  const answer = await resp.json();
  await pc.setRemoteDescription(answer);
}

function startWs() {
  ws = new WebSocket(`ws://${window.location.host}/ws/control`);
  ws.onerror = (e) => console.error("WS error", e);
}

function sendDrive(vx, steer) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ type: "drive", vx, steer }));
}

function sendEmergencyStop() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ type: "emergency_stop" }));
}

// ========== Camera Control ==========

let currentPan = 0.0;
let currentTilt = 0.0;

// Конфигурация (загружается с сервера)
let CAMERA_STEP = 0.1;  // дискретный шаг
let CAMERA_SPEED = 0.05;  // скорость плавного движения
let CAMERA_UPDATE_INTERVAL = 100;  // мс (10 Hz)
let CAMERA_HOLD_DELAY = 200;  // задержка перед плавным движением
let CAMERA_MIN = -1.0;
let CAMERA_MAX = 1.0;

let cameraMoveInterval = null;

async function loadConfig() {
  try {
    const resp = await fetch('/api/config');
    const cfg = await resp.json();

    // Обновляем настройки камеры из конфига
    CAMERA_STEP = cfg.camera.step;
    CAMERA_SPEED = cfg.camera.speed;
    CAMERA_UPDATE_INTERVAL = cfg.camera.update_interval_ms;
    CAMERA_HOLD_DELAY = cfg.camera.hold_delay_ms;
    CAMERA_MIN = Math.min(cfg.camera.min_pan, cfg.camera.min_tilt);
    CAMERA_MAX = Math.max(cfg.camera.max_pan, cfg.camera.max_tilt);

    console.log('[Config] Loaded:', cfg);
  } catch (err) {
    console.warn('[Config] Failed to load, using defaults:', err);
  }
}

function sendCamera(pan, tilt) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ type: "camera", pan, tilt }));

  // Обновляем отображение
  document.getElementById("pan-display").textContent = pan.toFixed(2);
  document.getElementById("tilt-display").textContent = tilt.toFixed(2);
}

function moveCamera(panDelta, tiltDelta) {
  currentPan = Math.max(CAMERA_MIN, Math.min(CAMERA_MAX, currentPan + panDelta));
  currentTilt = Math.max(CAMERA_MIN, Math.min(CAMERA_MAX, currentTilt + tiltDelta));
  sendCamera(currentPan, currentTilt);
}

function resetCamera() {
  currentPan = 0.0;
  currentTilt = 0.0;
  sendCamera(currentPan, currentTilt);
}

// Плавное движение при удержании
function startCameraMove(panDelta, tiltDelta) {
  stopCameraMove();

  // Первый шаг сразу
  moveCamera(panDelta, tiltDelta);

  // Продолжаем двигать пока кнопка удерживается
  cameraMoveInterval = setInterval(() => {
    moveCamera(panDelta, tiltDelta);
  }, CAMERA_UPDATE_INTERVAL);
}

function stopCameraMove() {
  if (cameraMoveInterval) {
    clearInterval(cameraMoveInterval);
    cameraMoveInterval = null;
  }
}

// Клик = дискретный шаг, удержание = плавное движение
function setupCameraButton(buttonId, panDelta, tiltDelta) {
  const btn = document.getElementById(buttonId);
  let clickTimeout = null;

  btn.addEventListener('mousedown', () => {
    // Сначала делаем дискретный шаг
    moveCamera(panDelta, tiltDelta);

    // Если кнопка удерживается, начинаем плавное движение
    clickTimeout = setTimeout(() => {
      startCameraMove(panDelta * CAMERA_SPEED / CAMERA_STEP,
                      tiltDelta * CAMERA_SPEED / CAMERA_STEP);
    }, CAMERA_HOLD_DELAY);
  });

  btn.addEventListener('mouseup', () => {
    if (clickTimeout) clearTimeout(clickTimeout);
    stopCameraMove();
  });

  btn.addEventListener('mouseleave', () => {
    if (clickTimeout) clearTimeout(clickTimeout);
    stopCameraMove();
  });

  // Поддержка touch-событий для мобильных
  btn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    moveCamera(panDelta, tiltDelta);
    clickTimeout = setTimeout(() => {
      startCameraMove(panDelta * CAMERA_SPEED / CAMERA_STEP,
                      tiltDelta * CAMERA_SPEED / CAMERA_STEP);
    }, CAMERA_HOLD_DELAY);
  });

  btn.addEventListener('touchend', (e) => {
    e.preventDefault();
    if (clickTimeout) clearTimeout(clickTimeout);
    stopCameraMove();
  });
}

window.addEventListener("load", async () => {
  videoEl.addEventListener("click", async () => {
    if (!autoplayResolved) {
      try {
        await videoEl.play();
        autoplayResolved = true;
      } catch (err) {
        console.error("Manual play() failed", err);
      }
    }
  });

  // Загружаем конфигурацию
  await loadConfig();

  startWebRTC().catch(console.error);
  startWs();

  document.getElementById("forward").onclick = () => sendDrive(1.0, 0.0);
  document.getElementById("backward").onclick = () => sendDrive(-1.0, 0.0);
  document.getElementById("left").onclick = () => sendDrive(0.5, -1.0);
  document.getElementById("right").onclick = () => sendDrive(0.5, 1.0);
  document.getElementById("stop").onclick = () => sendEmergencyStop();

  // Управление камерой
  setupCameraButton("cam-up", 0, CAMERA_STEP);
  setupCameraButton("cam-down", 0, -CAMERA_STEP);
  setupCameraButton("cam-left", -CAMERA_STEP, 0);
  setupCameraButton("cam-right", CAMERA_STEP, 0);

  document.getElementById("cam-home").onclick = () => resetCamera();
});
