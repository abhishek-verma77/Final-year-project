``` python
import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, join_room
import subprocess
import threading
import queue
from faster_whisper import WhisperModel
from faster_whisper.vad import VadOptions
import numpy as np
from sentence_transformers import SentenceTransformer, util
import signal
import time
import uuid
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# --- Load Models ---
whisper_model = WhisperModel("medium.en", device="cuda", compute_type="int8_float16")
relevance_model = SentenceTransformer('msmarco-distilbert-base-tas-b')
print("AI models loaded.")

# --- Globals ---
clients = {}
rooms = {}
PROFILES_FILE = 'job_profiles.json'
shutdown_timer = None

FILLER_WORDS = ['um', 'uh', 'er', 'ah', 'like', 'okay', 'right', 'so', 'you know']

# --- Helper Functions ---
def load_profiles():
    if not os.path.exists(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_profiles(profiles):
    with open(PROFILES_FILE, 'w') as f:
        json.dump(profiles, f, indent=4)

def new_session_state():
    return {
        'transcript': [],
        'question_buffer': "",
        'answer_buffer': "",
        'relevance_scores': [],
        'filler_words': {'interviewer': 0, 'candidate': 0},
    }

# --- Threads ---
def whisper_thread(sid, audio_queue, stop_event):
    vad_parameters = VadOptions(min_silence_duration_ms=700, speech_pad_ms=300)
    while not stop_event.is_set():
        try:
            audio_np = audio_queue.get(timeout=1)
            segments, _ = whisper_model.transcribe(
                audio_np, language="en", beam_size=5, vad_filter=True, vad_parameters=vad_parameters, no_speech_threshold=0.7
            )
            full_text = " ".join(segment.text for segment in segments).strip()
            
            if full_text and sid in clients:
                client_info = clients[sid]
                room_id = client_info['room']
                if room_id not in rooms: continue
                
                speaker_role = client_info['role']
                
                socketio.emit('transcript_update', {'speaker': speaker_role.capitalize(), 'text': full_text}, room=room_id)
                
                room_state = rooms[room_id]['state']
                room_state['transcript'].append({'speaker': speaker_role, 'text': full_text})

                if speaker_role == 'interviewer':
                    room_state['question_buffer'] += full_text + " "
                elif speaker_role == 'candidate':
                    room_state['answer_buffer'] += full_text + " "

                words = full_text.lower().split()
                for word in words:
                    cleaned_word = word.strip(".,?!")
                    if cleaned_word in FILLER_WORDS:
                        room_state['filler_words'][speaker_role] += 1
                socketio.emit('clarity_update', {'fillers': room_state['filler_words']}, room=room_id)
        except queue.Empty:
            continue

def ffmpeg_reader_thread(process, audio_queue, stop_event):
    while not stop_event.is_set():
        audio_chunk = process.stdout.read(32000)
        if not audio_chunk: break
        audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        audio_queue.put(audio_np)

# --- HTTP Routes ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/profiles')
def profiles_page():
    return render_template('profiles.html')

@app.route('/get_profiles')
def get_profiles():
    return jsonify(load_profiles())

@app.route('/add_profile', methods=['POST'])
def add_profile():
    data = request.json
    profiles = load_profiles()
    profiles[data['title']] = data['keywords']
    save_profiles(profiles)
    return jsonify({"status": "success"})

@app.route('/create_interview')
def create_interview():
    profile = request.args.get('profile')
    if not profile:
        return "Error: A profile must be selected.", 400
    room_id = str(uuid.uuid4())
    rooms[room_id] = {'interviewer': None, 'candidate': None, 'profile': profile, 'state': new_session_state()}
    return redirect(url_for('interview_room', room_id=room_id))

@app.route('/interview/<room_id>')
def interview_room(room_id):
    if room_id not in rooms:
        return "Interview session not found or has expired.", 404
    return render_template('index.html', room_id=room_id)

@app.route('/report/<room_id>')
def generate_report(room_id):
    if room_id not in rooms:
        return "Report not found or session expired.", 404
    
    room_data = rooms[room_id]
    room_state = room_data['state']
    profiles = load_profiles()
    profile_keywords = profiles.get(room_data['profile'], [])
    
    analysis = {"positive": "No specific positive points noted.", "improvement": "No specific areas for improvement noted."}
    
    candidate_text = " ".join([entry['text'] for entry in room_state['transcript'] if entry['speaker'] == 'candidate']).lower()
    mentioned_keywords = [kw for kw in profile_keywords if kw.lower() in candidate_text]
    if mentioned_keywords:
        analysis['positive'] = f"Candidate effectively discussed key skills: {', '.join(mentioned_keywords)}."
        
    avg_relevance = 0
    if room_state['relevance_scores']:
        avg_relevance = sum(room_state['relevance_scores']) / len(room_state['relevance_scores'])
        if avg_relevance < 50:
            analysis['improvement'] = "Candidate's answers were often not directly related to the questions asked, suggesting a potential lack of understanding or preparation."

    metrics = {
        "avg_relevance": round(avg_relevance),
        "filler_words": room_state['filler_words'],
        "keywords_mentioned": mentioned_keywords if mentioned_keywords else ["None"]
    }
    
    return render_template('report.html', 
                           profile_title=room_data['profile'],
                           transcript=room_state['transcript'],
                           metrics=metrics,
                           analysis=analysis)

# --- SocketIO Events ---
@socketio.on('connect')
def handle_connect():
    global shutdown_timer
    if shutdown_timer:
        shutdown_timer.cancel()
        shutdown_timer = None
        print("Shutdown timer cancelled.")
    
    sid = request.sid
    print(f'Client connected: {sid}')

@socketio.on('join')
def on_join(data):
    sid = request.sid
    room_id = data['room']
    if room_id not in rooms: return
    join_room(room_id)
    
    role = 'interviewer' if rooms[room_id]['interviewer'] is None else 'candidate'
    rooms[room_id][role] = sid
    
    clients[sid] = {
        'room': room_id, 'role': role,
        'ffmpeg_process': subprocess.Popen(['ffmpeg', '-i', 'pipe:0', '-f', 's16le', '-ac', '1', '-ar', '16000', 'pipe:1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE),
        'audio_queue': queue.Queue(), 'stop_event': threading.Event()
    }
    clients[sid]['whisper_thread'] = threading.Thread(target=whisper_thread, args=(sid, clients[sid]['audio_queue'], clients[sid]['stop_event']))
    clients[sid]['ffmpeg_thread'] = threading.Thread(target=ffmpeg_reader_thread, args=(clients[sid]['ffmpeg_process'], clients[sid]['audio_queue'], clients[sid]['stop_event']))
    clients[sid]['whisper_thread'].start()
    clients[sid]['ffmpeg_thread'].start()
    
    socketio.emit('assign_role', {'role': role}, room=sid)

@socketio.on('trigger_score')
def on_trigger_score(data):
    sid = request.sid
    if sid not in clients: return
    room_id = clients[sid]['room']
    if room_id not in rooms: return
    room_state = rooms[room_id]['state']

    if room_state['question_buffer'] and room_state['answer_buffer']:
        q_embedding = relevance_model.encode(room_state['question_buffer'], convert_to_tensor=True)
        a_embedding = relevance_model.encode(room_state['answer_buffer'], convert_to_tensor=True)
        
        cosine_score = util.pytorch_cos_sim(q_embedding, a_embedding).item()
        score_percent = round(max(0, cosine_score) * 100)
        
        room_state['relevance_scores'].append(score_percent)
        socketio.emit('relevance_score', {'score': score_percent}, room=room_id)
        
        room_state['question_buffer'] = ""
        room_state['answer_buffer'] = ""

@socketio.on('audio_data')
def handle_audio_data(audio_chunk):
    sid = request.sid
    if sid in clients:
        try:
            clients[sid]['ffmpeg_process'].stdin.write(audio_chunk)
        except (BrokenPipeError, OSError):
            cleanup_client_resources(sid)

def shutdown_server():
    print("No clients connected. Shutting down server...")
    os.kill(os.getpid(), signal.SIGINT)

@socketio.on('disconnect')
def handle_disconnect():
    global shutdown_timer
    sid = request.sid
    print(f"Client is disconnecting: {sid}")
    cleanup_client_resources(sid)
    
    # Check if the clients dictionary is empty *after* cleanup
    if not clients:
        print("Last client disconnected. Server will shut down in 5 seconds.")
        shutdown_timer = threading.Timer(5.0, shutdown_server)
        shutdown_timer.start()

def cleanup_client_resources(sid):
    if sid in clients:
        client_info = clients[sid]
        room_id = client_info['room']
        
        client_info['stop_event'].set()
        if client_info['ffmpeg_process'].stdin: client_info['ffmpeg_process'].stdin.close()
        client_info['whisper_thread'].join(timeout=2)
        client_info['ffmpeg_thread'].join(timeout=2)
        if client_info['ffmpeg_process'].poll() is None: client_info['ffmpeg_process'].terminate()
        
        if sid in clients: del clients[sid]
        print(f"Cleaned up resources for client {sid}")
        
        if room_id in rooms:
            if rooms[room_id]['interviewer'] == sid: rooms[room_id]['interviewer'] = None
            elif rooms[room_id]['candidate'] == sid: rooms[room_id]['candidate'] = None
            
            # Check if all roles in the room are now empty
            if all(value is None for key, value in rooms[room_id].items() if key in ['interviewer', 'candidate']):
                del rooms[room_id]
                print(f"Room {room_id} is empty and has been deleted.")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
```
