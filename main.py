import os
import sys
import time
import threading
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Controller as KeyboardController
from modules.voice_assistant import VoiceAssistant
from modules.gesture_recognition import GestureRecognition
from modules.system_control import SystemControl
from modules.ai_connector import AIConnector
from ai_integrations.chatgpt_connector import ChatGPTConnector
from ai_integrations.gemini_connector import GeminiConnector
from cloud.aws_integration import AWSIntegration
from monitoring.cpu_usage import CPUUsageMonitor
from monitoring.analytics_dashboard import AnalyticsDashboard
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger("Devin")

# Mouse and keyboard controllers
mouse = MouseController()
keyboard = KeyboardController()

# Global assistant configuration
assistant_name = "Devin"
wake_word = f"Hey {assistant_name}"
user_voice_id = "user123"  # Replace with unique user voice ID

# Initialize AI modules
chatgpt = ChatGPTConnector(api_key=os.getenv("CHATGPT_API_KEY"))
gemini = GeminiConnector(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize system modules
voice_assistant = VoiceAssistant(wake_word, user_voice_id)
gesture_recognizer = GestureRecognizer()
system_controller = SystemController()
cpu_monitor = CPUUsageMonitor()
analytics_dashboard = AnalyticsDashboard()

# Cloud integrations
aws_integration = AWSIntegration()

# Define tasks
def handle_voice_command(command):
    """
    Process voice commands and execute corresponding tasks.
    """
    try:
        logger.info(f"Received voice command: {command}")
        if "open browser" in command:
            system_controller.open_application("browser")
        elif "shutdown system" in command:
            system_controller.shutdown()
        elif "control mouse" in command:
            control_mouse_with_gesture()
        else:
            response = chatgpt.get_response(command)
            logger.info(f"ChatGPT response: {response}")
            voice_assistant.speak(response)
    except Exception as e:
        logger.error(f"Error handling voice command: {e}")
        voice_assistant.speak("Sorry, I encountered an error processing your command.")

def control_mouse_with_gesture():
    """
    Enable gesture-based mouse control.
    """
    logger.info("Activating gesture-based mouse control...")
    voice_assistant.speak("Gesture-based mouse control activated. Use hand gestures to control the pointer.")
    gesture_recognizer.start_recognition(mouse)

def monitor_resources():
    """
    Monitor system resources and provide insights.
    """
    while True:
        cpu_usage = cpu_monitor.get_cpu_usage()
        logger.info(f"CPU usage: {cpu_usage}%")
        if cpu_usage > 90:
            voice_assistant.speak("Warning: CPU usage is critically high!")
        time.sleep(10)

def perform_cloud_tasks():
    """
    Handle cloud-related tasks.
    """
    try:
        logger.info("Performing cloud operations...")
        aws_integration.sync_files()
    except Exception as e:
        logger.error(f"Cloud operation error: {e}")

def keyboard_typing_simulation(text):
    """
    Simulate keyboard typing for automation tasks.
    """
    logger.info(f"Typing text: {text}")
    for char in text:
        keyboard.type(char)
        time.sleep(0.1)

# Main loop
def main():
    logger.info(f"Starting {assistant_name}...")
    voice_assistant.speak(f"Hello! {assistant_name} is ready.")
    
    # Start monitoring in a separate thread
    threading.Thread(target=monitor_resources, daemon=True).start()
    
    # Listen for commands
    while True:
        try:
            command = voice_assistant.listen()
            if wake_word.lower() in command.lower():
                command = command.replace(wake_word, "").strip()
                handle_voice_command(command)
        except KeyboardInterrupt:
            logger.info("Shutting down Devin...")
            voice_assistant.speak("Goodbye!")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            voice_assistant.speak("An unexpected error occurred.")

if __name__ == "__main__":
    main()
