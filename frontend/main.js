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
    console.log("ontrack: received stream", stream);
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

    // Debug: check track state every 2 seconds
    setInterval(() => {
      const tracks = videoEl.srcObject?.getVideoTracks();
      if (tracks && tracks.length > 0) {
        console.log("videoTrack readyState:", tracks[0].readyState, "muted:", tracks[0].muted, "enabled:", tracks[0].enabled);
      }
    }, 2000);
  };

  pc.oniceconnectionstatechange = () => {
    console.log("iceConnectionState:", pc.iceConnectionState);
  };

  pc.onconnectionstatechange = () => {
    console.log("connectionState:", pc.connectionState);
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
  ws.onopen = () => console.log("WS open");
  ws.onclose = () => console.log("WS closed");
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

window.addEventListener("load", () => {
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

  startWebRTC().catch(console.error);
  startWs();

  document.getElementById("forward").onclick = () => sendDrive(1.0, 0.0);
  document.getElementById("backward").onclick = () => sendDrive(-1.0, 0.0);
  document.getElementById("left").onclick = () => sendDrive(0.5, -1.0);
  document.getElementById("right").onclick = () => sendDrive(0.5, 1.0);
  document.getElementById("stop").onclick = () => sendEmergencyStop();
});
