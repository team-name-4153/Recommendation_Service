from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
import asyncio
from app import socketio
from flask_socketio import emit
from flask import request

pcs = {}
broadcast_pc = None

# Handle broadcaster's offer
@socketio.on('broadcaster_offer')
async def handle_broadcaster_offer(data):
    global broadcast_pc
    broadcast_pc = RTCPeerConnection()
    pcs['broadcaster'] = broadcast_pc

    @broadcast_pc.on('track')
    def on_track(track):
        print(f"Broadcaster track received: {track.kind}")
        # Forward the track to all viewers
        for sid, pc in pcs.items():
            if sid != 'broadcaster':
                pc.addTrack(track)

    offer = RTCSessionDescription(sdp=data['sdp'], type=data['type'])
    await broadcast_pc.setRemoteDescription(offer)
    answer = await broadcast_pc.createAnswer()
    await broadcast_pc.setLocalDescription(answer)

    emit('broadcaster_answer', {
        'sdp': broadcast_pc.localDescription.sdp,
        'type': broadcast_pc.localDescription.type
    })

# Handle viewer's offer
@socketio.on('viewer_offer')
async def handle_viewer_offer(data):
    sid = request.sid
    pc = RTCPeerConnection()
    pcs[sid] = pc

    @pc.on('icecandidate')
    def on_icecandidate(event):
        if event.candidate:
            emit('viewer_candidate', {'candidate': event.candidate}, room=sid)

    # Add tracks from the broadcaster to the viewer
    if broadcast_pc and broadcast_pc.getTransceivers():
        for transceiver in broadcast_pc.getTransceivers():
            pc.addTransceiver(
                kind=transceiver.kind,
                direction=transceiver.direction,
                streams=transceiver.streams
            )

    offer = RTCSessionDescription(sdp=data['sdp'], type=data['type'])
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    emit('viewer_answer', {
        'sdp': pc.localDescription.sdp,
        'type': pc.localDescription.type
    }, room=sid)

# Handle ICE candidates
@socketio.on('candidate')
async def handle_candidate(data):
    sid = request.sid
    candidate = RTCIceCandidate(
        candidate=data['candidate'],
        sdpMid=data['sdpMid'],
        sdpMLineIndex=data['sdpMLineIndex']
    )
    role = data.get('role')
    if role == 'broadcaster' and broadcast_pc:
        await broadcast_pc.addIceCandidate(candidate)
    elif sid in pcs:
        await pcs[sid].addIceCandidate(candidate)

# Clean up on disconnect
@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in pcs:
        pc = pcs.pop(sid)
        asyncio.ensure_future(pc.close())
