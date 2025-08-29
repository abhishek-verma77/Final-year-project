# **Project CLAIRE: A Cognitive Language and Interview Relevance Engine**
CLAIRE (Cognitive Language and Interview Relevance Engine) is a real-time web application designed to act as an intelligent co-pilot for interviewers. It runs alongside any video conferencing tool to provide a layer of objective, data-driven analysis on the conversation, helping to reduce bias and improve the quality of technical interview evaluations.

The project has evolved from a simple local script into a full-fledged, multi-user web application that manages the entire interview lifecycle, from job profile creation to a final, customized performance report.

## **Key Features**
1. 👥 Multi-User Interview Rooms: An interviewer can create a unique, shareable link for a candidate to join a shared session from anywhere in the world.

2. 🤖 Automatic Speaker Identification: The system automatically identifies and labels the transcript based on who created the session (Interviewer) versus who joined (Candidate).

3. 📝 Live, High-Accuracy Transcription: Utilizes the Whisper medium.en model via faster-whisper to provide a real-time transcript of the conversation for both participants, bridging communication gaps.

4. 🧠 Real-time Answer Relevance Score (Core Innovation): Employs a specialized SentenceTransformer model to analyze the semantic meaning of the interviewer's question and the candidate's answer, generating a live score that quantifies how well the answer addressed the question.

## **📊 Clarity & Keyword Metrics:**

* Tracks the usage of common filler words for both speakers.

* Analyzes the final transcript against pre-defined keywords for a specific job profile.

* 📋 Profile Management & Final Reporting:

* Allows interviewers to create and save job profiles with specific keywords.

* Generates a comprehensive, customized HTML report after the interview, summarizing key metrics, AI-generated analysis, and the full transcript.

## **System Architecture**
The application uses a robust client-server model to handle real-time audio processing efficiently:

1. **Frontend (Browser):** The user's browser accesses the microphone using the standard WebRTC API. It captures audio and streams it in 3-second chunks over a persistent WebSocket connection. The entire UI is built with HTML and JavaScript.

2. **Backend (Python Server):**

  * A Flask-SocketIO server manages user sessions, unique interview rooms, and all real-time communication.

  * The backend handles multiple HTTP routes for the home page, profile management, and report generation.

  * For each user, a dedicated FFmpeg process is spawned to convert the browser's audio into a standardized raw audio format (16-bit PCM @ 16kHz).

3. A multi-threaded pipeline feeds the converted audio into the Whisper model for transcription and the Sentence Transformer model for analysis.

## **Technology Stack**
### **Backend Framework**

1. Python 3.11

2. **Flask:** For handling HTTP requests and serving the application.

3. **Flask-SocketIO:** For real-time, two-way communication using WebSockets.

4. **Artificial Intelligence / Machine Learning**

  * Transcription: faster-whisper (medium.en model) with VAD filtering.

  * Semantic Analysis: sentence-transformers (msmarco-distilbert-base-tas-b model).

  * Core Libraries: PyTorch, NumPy

5. **Frontend (Client-Side)**

* HTML & CSS: For the structure and styling of the web interface.

* JavaScript: For all user interactions, microphone access (WebRTC), and communication with the server.

* Audio Processing

* FFmpeg: For reliable, real-time audio format conversion on the server.

* Data Storage

6. **JSON:** A simple job_profiles.json file is used to persist job titles and keywords.

## **Setup and Installation**
### **Prerequisites:**

* Anaconda (or Miniconda)

* A CUDA-enabled NVIDIA GPU (for optimal performance)

* FFmpeg installed and added to your system's PATH.

1. Create the Conda Environment:
Open the Anaconda Prompt and create a new, clean environment with Python 3.11.

Bash

conda create -n claire_final python=3.11

2. Activate the Environment:

Bash

conda activate claire_final

3. Clone the repository:

Bash

git clone https://github.com/your-username/project-claire.git
cd project-claire

4. Install dependencies:
Create a requirements.txt file with the specified packages and run:

Bash

python -m pip install -r requirements.txt
5. Run the application:

Bash

python app.py
The server will start, and you can access the application by navigating to http://127.0.0.1:5000 in your web browser.

## **How to Use**
1. Start the Server: Run python app.py.

2. Manage Profiles: Open http://127.0.0.1:5000 and you will be directed to the home page. Click "Manage & Start Interviews" to go to the profiles page. Here you can create a new job profile or select an existing one.

3. Start the Interview: After selecting a profile, click "Start Interview with this Profile." You will be redirected to a unique interview room and will be assigned the "Interviewer" role.

4. Invite the Candidate: Copy the unique URL from your browser's address bar and send it to the candidate. When they open it, they will automatically join as the "Candidate."

5. Begin the Session: Both you and the candidate must click the "Start Session" button on your respective pages to activate your microphones.

6. Conduct the Interview: The transcript will appear live for both users. As the interviewer, you can click "Calculate Relevance Score" after the candidate has answered a question.

7. Generate Report: After clicking "Stop Session," the interviewer can click "Generate Final Report" to see a complete summary of the interview in a new tab.

## **Project Roadmap (Future Scope)**
* [ ] 🤖 Fully Automated Speaker Diarization: Replace the current role-assignment system with a real-time pyannote.audio model to automatically detect who is speaking at any given moment, even with more than two participants.

* [ ] 🔑 Live Keyword Highlighting: Highlight the pre-defined job keywords directly in the live transcript as they are spoken.

* [ ] ☁️ Cloud Deployment: Deploy the application to a cloud service like AWS or Heroku to provide a permanent, publicly accessible URL without needing to run ngrok.

[ ] 💾 Database Integration: Replace the job_profiles.json file and in-memory session data with a proper database (like PostgreSQL or MongoDB) to allow for persistent storage and analysis of interview data over time.
