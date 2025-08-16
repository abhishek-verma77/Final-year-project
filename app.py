
import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

from flask import Flask, render_template, request
from flask_socketio import SocketIO
import subprocess
import threading
import queue
from faster_whisper import WhisperModel
import numpy as np
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Load Transcription Model
whisper_model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
print("Transcription model loaded.")

# Load Sentence Transformer Model for relevance scoring
relevance_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Relevance scoring model loaded.")

clients = {}

def whisper_thread(sid, audio_queue, stop_event):
    vad_parameters = {"min_silence_duration_ms": 500}
    while not stop_event.is_set():
        try:
            audio_np = audio_queue.get(timeout=1)
            segments, _ = whisper_model.transcribe(
                audio_np, 
                language="en",
                beam_size=5,
                vad_filter=True,
                vad_parameters=vad_parameters
            )
            
            full_text = " ".join(segment.text for segment in segments).strip()
            
            if full_text and sid in clients:
                state = clients[sid]['state']
                speaker = state['current_speaker']
                
                # Emit the transcript with the current speaker
                socketio.emit('transcript_update', {'speaker': speaker.capitalize() if speaker else 'Unknown', 'text': full_text}, room=sid)
                
                # Append text to the correct buffer
                if speaker == 'interviewer':
                    state['question_buffer'] += full_text + " "
                elif speaker == 'candidate':
                    state['answer_buffer'] += full_text + " "
        except queue.Empty:
            continue

def ffmpeg_reader_thread(process, audio_queue, stop_event):
    while not stop_event.is_set():
        audio_chunk = process.stdout.read(32000)
        if not audio_chunk: break
        audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        audio_queue.put(audio_np)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    print(f'Client connected: {sid}')
    ffmpeg_command = ['ffmpeg', '-i', 'pipe:0', '-f', 's16le', '-ac', '1', '-ar', '16000', 'pipe:1']
    clients[sid] = {
        'ffmpeg_process': subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE),
        'audio_queue': queue.Queue(),
        'stop_event': threading.Event(),
        'state': {
            'current_speaker': None,
            'question_buffer': "",
            'answer_buffer': ""
        }
    }
    clients[sid]['whisper_thread'] = threading.Thread(target=whisper_thread, args=(sid, clients[sid]['audio_queue'], clients[sid]['stop_event']))
    clients[sid]['ffmpeg_thread'] = threading.Thread(target=ffmpeg_reader_thread, args=(clients[sid]['ffmpeg_process'], clients[sid]['audio_queue'], clients[sid]['stop_event']))
    clients[sid]['whisper_thread'].start()
    clients[sid]['ffmpeg_thread'].start()

@socketio.on('speaker_change')
def handle_speaker_change(data):
    sid = request.sid
    if sid not in clients: return
    
    state = clients[sid]['state']
    new_speaker = data['speaker']
    
    # If the interviewer starts speaking after the candidate, calculate the score
    if state['current_speaker'] == 'candidate' and new_speaker == 'interviewer':
        if state['question_buffer'] and state['answer_buffer']:
            print("Calculating relevance score...")
            q_embedding = relevance_model.encode(state['question_buffer'], convert_to_tensor=True)
            a_embedding = relevance_model.encode(state['answer_buffer'], convert_to_tensor=True)
            
            cosine_score = util.pytorch_cos_sim(q_embedding, a_embedding).item()
            score_percent = round(max(0, cosine_score) * 100)
            
            socketio.emit('relevance_score', {'score': score_percent}, room=sid)
            
            # Reset buffers for the next Q&A
            state['question_buffer'] = ""
            state['answer_buffer'] = ""
    
    state['current_speaker'] = new_speaker
    print(f"Speaker for {sid} changed to: {new_speaker}")

@socketio.on('audio_data')
def handle_audio_data(audio_chunk):
    sid = request.sid
    if sid in clients:
        try:
            clients[sid]['ffmpeg_process'].stdin.write(audio_chunk)
        except (BrokenPipeError, OSError):
            cleanup_client_resources(sid)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    cleanup_client_resources(sid)

def cleanup_client_resources(sid):
    if sid in clients:
        client = clients[sid]
        client['stop_event'].set()
        if client['ffmpeg_process'].stdin: client['ffmpeg_process'].stdin.close()
        client['whisper_thread'].join(timeout=2)
        client['ffmpeg_thread'].join(timeout=2)
        if client['ffmpeg_process'].poll() is None: client['ffmpeg_process'].terminate()
        del clients[sid]
        print(f"Cleaned up resources for client {sid}")

if __name__ == '__main__':
    print("─" * 40)
    print("Server is running!")
    print("Open this link in your browser:")
    print("http://127.0.0.1:5000")
    print("─" * 40)
    socketio.run(app, host='0.0.0.0', port=5000)