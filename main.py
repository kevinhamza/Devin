"""
DO NOT REARRANGE THE ORDER OF FUNCTION CALLS AND VARIABLE DECLARATIONS
AS IT MAY CAUSE IMPORT ERRORS AND OTHER ISSUES
"""
from gevent import monkey
monkey.patch_all()

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from threading import Thread
import tiktoken
import speech_recognition as sr
import pyttsx3

# Custom modules from your folder structure
from modules.server import ServerManager
from monitoring.analytics_dashboard import SystemMonitor
from security.threat_modeling import ThreatDetection
from cloud.private_cloud_integration import CloudManager
from plugins.speech_recognition import SpeechRecognizer
from backups.config_backup import BackupManager
from prototypes.neural_network import NeuralNetworkPrototype
from config.other import Config
from scripts.generate_ssl_certificate import SSLManager
from databases.pentest_results import PentestResults
from core_service import CoreService

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://localhost:3000", "http://localhost:3000"]}})

# Logging configuration
log = logging.getLogger("werkzeug")
log.disabled = True

# Initialize modules
TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

server_manager = ServerManager()
system_monitor = SystemMonitor()
threat_detection = ThreatDetection()
cloud_manager = CloudManager()
speech_recognizer = SpeechRecognizer()
backup_manager = BackupManager()
neural_network = NeuralNetworkPrototype()
config = Config()
ssl_manager = SSLManager()
pentest_results = PentestResults()
core_service = CoreService()

# Speech and voice setup
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen_to_voice():
    try:
        with sr.Microphone() as source:
            speak("Listening for your command.")
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio)
            return command.lower()
    except Exception as e:
        logging.error(f"Voice recognition error: {e}")
        return None

@app.route("/api/system-monitor", methods=["GET"])
def get_system_stats():
    stats = system_monitor.collect_stats()
    return jsonify(stats)

@app.route("/api/threat-detection", methods=["POST"])
def detect_threats():
    data = request.json
    threat_report = threat_detection.analyze(data)
    return jsonify(threat_report)

@app.route("/api/cloud-management", methods=["POST"])
def manage_cloud():
    data = request.json
    response = cloud_manager.handle_request(data)
    return jsonify(response)

@app.route("/api/voice-command", methods=["GET"])
def voice_command():
    command = listen_to_voice()
    if command:
        response = server_manager.execute(command)
        speak(response.get("message", "Command executed"))
        return jsonify(response)
    else:
        return jsonify({"error": "Could not understand the voice command"})

@app.route("/api/logs", methods=["GET"])
def logs():
    logs = backup_manager.get_logs()
    return jsonify({"logs": logs})

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "Devin is running!"})

@app.route("/api/neural-network", methods=["POST"])
def neural_network_task():
    data = request.json
    task_result = neural_network.run_task(data)
    return jsonify({"result": task_result})

if __name__ == "__main__":
    logging.info("Devin is up and running!")
    speak("Devin is ready for your commands.")
    app.run(debug=False, port=1337, host="0.0.0.0")
