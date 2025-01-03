import os
import sys
import logging
from modules.voice_assistant import VoiceAssistant
from modules.system_control import SystemControl
from modules.gesture_recognition import GestureRecognition
from modules.ai_tools.ai_learning import AILearning
from operate.analytics import Analytics
from cloud.aws_integration import AWSIntegration
from cloud.gcp_integration import GCPIntegration
from cloud.azure_integration import AzureIntegration
from monitoring.cpu_usage import CPUUsage
from monitoring.analytics_dashboard import AnalyticsDashboard
from scripts.initialize_db import initialize_database
from scripts.update_firmware import FirmwareUpdater
from security.threat_modeling import ThreatModeling
from modules.nlp_conversation import NLPConversation
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_services():
    """Initialize all required services and dependencies."""
    try:
        # Retrieve arguments from .env file
        db_path = os.getenv("DB_PATH", "")
        data_key = os.getenv("DATA_KEY", "")
        firmware_url = os.getenv("FIRMWARE_URL", "")
        firmware_version = os.getenv("FIRMWARE_VERSION", "")
        backup_path = os.getenv("BACKUP_PATH", "")

        # Debug: Check the values of the environment variables
        logger.debug(f"DB_PATH: {db_path}")
        logger.debug(f"DATA_KEY: {data_key}")
        logger.debug(f"FIRMWARE_URL: {firmware_url}")
        logger.debug(f"FIRMWARE_VERSION: {firmware_version}")
        logger.debug(f"BACKUP_PATH: {backup_path}")

        # Check if any required variables are missing
        if not db_path:
            logger.error("DB_PATH is not set or is empty in the environment variables.")
            sys.exit(1)
        
        if not data_key:
            logger.error("DATA_KEY is not set or is empty in the environment variables.")
            sys.exit(1)

        if not firmware_url or not firmware_version or not backup_path:
            logger.error("Firmware configuration (URL, version, or backup path) is missing in the environment variables.")
            sys.exit(1)

        logger.info("Initializing database...")
        initialize_database(db_path, data_key)  # Pass db_path and data_key
        
        logger.info("Updating firmware...")
        firmware_updater = FirmwareUpdater(firmware_url, firmware_version, backup_path)
        firmware_updater.update()  # Call the firmware update method
        
        logger.info("Setting up cloud integrations...")
        AWSIntegration.setup()
        GCPIntegration.setup()
        AzureIntegration.setup()

        logger.info("Initializing monitoring tools...")
        CPUUsage.start_monitoring()
        AnalyticsDashboard.initialize()

        logger.info("Loading AI learning module...")
        AILearning.load_models()

        logger.info("Initializing system control module...")
        SystemControl.initialize()

        logger.info("System initialization complete.")
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        sys.exit(1)

def main():
    """Main function to run Devin's AI assistant."""
    logger.info("Starting Devin AI assistant...")

    # Initialize services
    initialize_services()

    # Load modules
    voice_assistant = VoiceAssistant()
    gesture_recognition = GestureRecognition()
    nlp_conversation = NLPConversation()

    # Main event loop
    while True:
        try:
            logger.info("Listening for user input...")

            # Voice assistant activation
            if voice_assistant.detect_wake_word():
                command = voice_assistant.listen_and_transcribe()
                logger.debug(f"User command: {command}")

                if "exit" in command.lower():
                    logger.info("Exiting Devin AI assistant.")
                    break

                response = nlp_conversation.process_command(command)
                logger.debug(f"Response: {response}")
                voice_assistant.speak(response)

            # Gesture recognition activation
            if gesture_recognition.detect_gesture():
                logger.info("Gesture recognized. Executing corresponding action.")
                gesture_recognition.execute_action()

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt detected. Exiting Devin AI assistant.")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    main()
