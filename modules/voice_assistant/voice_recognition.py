"""
voice_recognition.py
---------------------
This module handles the recognition of voice commands, leveraging advanced speech-to-text models for accuracy.

Dependencies:
- vosk (Speech-to-text recognition)
- sounddevice (Audio recording)
- numpy (Audio processing)
- logging (Log operations)
"""

import sounddevice as sd
import vosk
import numpy as np
import json
import os
import logging


class VoiceRecognition:
    """
    A class to handle voice command recognition.
    """

    def __init__(self, model_path="models/vosk_model", sample_rate=16000, log_file="voice_recognition.log"):
        """
        Initializes the VoiceRecognition system.

        Args:
            model_path (str): Path to the Vosk speech-to-text model.
            sample_rate (int): Sampling rate for audio recording.
            log_file (str): Path to the log file.
        """
        self.sample_rate = sample_rate
        self.model_path = model_path
        self.log_file = log_file

        # Setup logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        logging.info("VoiceRecognition initialized.")

        # Load the Vosk model
        if not os.path.exists(self.model_path):
            logging.error(f"Model path does not exist: {self.model_path}")
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        try:
            self.model = vosk.Model(model_path)
            logging.info(f"Vosk model loaded from {self.model_path}.")
        except Exception as e:
            logging.error(f"Failed to load Vosk model: {e}")
            raise

    def record_audio(self, duration=5):
        """
        Records audio from the microphone.

        Args:
            duration (int): Duration in seconds.

        Returns:
            np.ndarray: Recorded audio as a numpy array.
        """
        logging.info(f"Recording audio for {duration} seconds...")
        try:
            audio = sd.rec(int(duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype="float32")
            sd.wait()  # Wait for the recording to finish
            logging.info("Audio recording completed.")
            return np.squeeze(audio)
        except Exception as e:
            logging.error(f"Audio recording failed: {e}")
            raise

    def recognize_voice(self, duration=5):
        """
        Recognizes voice commands from recorded audio.

        Args:
            duration (int): Duration in seconds for recording audio.

        Returns:
            str: Recognized text from the voice command.
        """
        logging.info("Starting voice recognition...")
        try:
            audio = self.record_audio(duration)
            audio_data = (audio * 32767).astype(np.int16).tobytes()  # Convert to 16-bit PCM

            # Initialize recognizer
            recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

            if recognizer.AcceptWaveform(audio_data):
                result = json.loads(recognizer.Result())
                recognized_text = result.get("text", "")
                logging.info(f"Recognized text: {recognized_text}")
                return recognized_text
            else:
                logging.warning("Could not recognize any text from the audio.")
                return ""
        except Exception as e:
            logging.error(f"Voice recognition failed: {e}")
            raise

    def listen_and_process(self):
        """
        Continuously listens for voice commands and processes them.

        Returns:
            str: Recognized command text.
        """
        print("Listening for commands. Speak now.")
        try:
            recognized_text = self.recognize_voice()
            if recognized_text:
                logging.info(f"Command received: {recognized_text}")
                print(f"You said: {recognized_text}")
            else:
                print("No command recognized.")
            return recognized_text
        except Exception as e:
            logging.error(f"Error during listen and process: {e}")
            print("An error occurred. Please try again.")
            return ""

if __name__ == "__main__":
    # Example usage
    model_dir = "models/vosk_model"
    recognizer = VoiceRecognition(model_path=model_dir)

    print("1. Record and recognize a single command")
    print("2. Continuously listen and recognize commands")
    choice = input("Enter your choice (1/2): ")

    if choice == "1":
        print("Recording a single command...")
        try:
            command = recognizer.recognize_voice(duration=5)
            if command:
                print(f"Recognized command: {command}")
            else:
                print("No command recognized.")
        except Exception as e:
            print(f"Error: {e}")
    elif choice == "2":
        recognizer.listen_and_process()
    else:
        print("Invalid choice. Exiting.")
