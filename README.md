Project CLAIRE: A Cognitive Language and Interview Relevance Engine
CLAIRE (Cognitive Language and Interview Relevance Engine) is a real-time web application designed to act as an intelligent co-pilot for interviewers. It runs alongside any video conferencing tool to provide a layer of objective, data-driven analysis on the conversation, helping to reduce bias and improve the quality of technical interview evaluations.

The Problem
Traditional interviews are often hampered by subjectivity, cognitive overload, and communication barriers. An interviewer must simultaneously manage the conversation, take notes, and evaluate complex concepts, which can lead to inconsistent and biased assessments. Project CLAIRE aims to solve this by handling the objective analysis, allowing the interviewer to focus on the candidate.

(A GIF demonstrating the live transcription and relevance score would go here)
![CLAIRE Demo GIF]

Key Features
🎤 Live, High-Accuracy Transcription: Utilizes the Whisper large-v3 model via faster-whisper to provide a real-time transcript of the conversation for both interviewer and candidate.

🧠 Real-time Answer Relevance Score (Core Innovation): Employs a SentenceTransformer model to analyze the semantic meaning of the interviewer's question and the candidate's answer, generating a live score that quantifies how well the answer addressed the question.

🌐 Cross-Platform Web Application: Built with a robust client-server architecture (Flask & WebSockets) that bypasses local audio driver issues and runs on any modern web browser.

🗣️ Speaker State Management: A UI for manually selecting the current speaker (Interviewer/Candidate) to correctly attribute text and trigger analysis.

System Architecture
The application uses a client-server model to handle real-time audio processing efficiently:

Frontend (Browser): The user's browser accesses the microphone using the standard WebRTC API. It captures audio and streams it in 5-second chunks over a persistent WebSocket connection.

Backend (Python Server):

A Flask-SocketIO server receives the audio chunks from each connected client.

The audio is piped into a dedicated FFmpeg process for each user, which converts it into a standardized raw audio format (16-bit PCM @ 16kHz).

A multi-threaded pipeline feeds the converted audio into the Whisper model for transcription.

The transcribed text is then sent back to the browser to be displayed and is stored in a buffer for analysis.

When the speaker state changes, the Sentence Transformer model is triggered to calculate the relevance score, which is then sent to the browser.

Technology Stack
Backend: Python 3.11, Flask, Flask-SocketIO

AI / Machine Learning:

Transcription: faster-whisper (large-v3 model)

Semantic Analysis: sentence-transformers (all-MiniLM-L6-v2 model)

Core Libraries: PyTorch, NumPy

Frontend: HTML, JavaScript (WebRTC, Socket.IO Client)

Audio Processing: FFmpeg

**Setup and Installation**
Prerequisites:

Python 3.11

A CUDA-enabled NVIDIA GPU (for optimal performance)

FFmpeg installed and added to your system's PATH.

1. Clone the repository:

git clone https://github.com/your-username/project-claire.git
cd project-claire

2. Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

3. Install dependencies:

pip install -r requirements.txt

(Note: You will need to create a requirements.txt file with all the necessary libraries)

4. Run the application:

python app.py

The server will start, and you can access the application by navigating to http://127.0.0.1:5000 in your web browser.

How to Use
Open the web application in your browser.

Click "Start Session" and allow microphone access.

Use the "Interviewer Speaking" and "Candidate Speaking" buttons to indicate who is talking.

To get a relevance score, follow this sequence:

Click "Interviewer Speaking" and ask a question.

Click "Candidate Speaking" and provide an answer.

Click "Interviewer Speaking" again to trigger the analysis. The score will appear on the right.

Click "Stop Session" to end the transcription.

Project Roadmap (Future Work)
[ ] 🤖 Automatic Speaker Diarization: Replace the manual speaker selection buttons with an automated diarization model (pyannote.audio) to detect who is speaking automatically.

[ ] 👥 Multi-user Sessions: Implement a "room" system so that an interviewer and candidate can join a shared session from different computers.

[ ] 📊 Communication Clarity Metrics: Add analytics to track filler word usage and the talk-time ratio between speakers.

[ ] 📄 Post-Interview Report: Create a feature to generate a downloadable summary of the interview, including the full transcript and all calculated metrics.
