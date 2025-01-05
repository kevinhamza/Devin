"""
wake_word_detection.py
----------------------
This module detects the wake word "Hey Devin" using the Porcupine library.

Dependencies:
- pvporcupine (Wake word detection)
- pyaudio (Audio input)
- logging (Error and event logging)
"""

import pvporcupine
import pyaudio
import struct
import os
import logging
from threading import Thread


class WakeWordDetector:
    """
    Detects the wake word 'Hey Devin' using the Porcupine library.
    """

    def __init__(self, keyword_model_path, sensitivity=0.5, access_key=None, log_file="wake_word_detection.log"):
        """
        Initializes the WakeWordDetector.

        Args:
            keyword_model_path (str): Path to the keyword model file for "Hey Devin."
            sensitivity (float): Sensitivity level for wake word detection (0 to 1).
            access_key (str): Picovoice Access Key.
            log_file (str): Path to the log file for recording events and errors.
        """
        if access_key is None:
            raise ValueError("An access key is required for Porcupine initialization.")

        self.keyword_model_path = keyword_model_path
        self.sensitivity = sensitivity
        self.access_key = access_key
        self.log_file = log_file
        self.running = False
        self.stream = None

        # Setup logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

        # Initialize Porcupine
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[self.keyword_model_path],
                sensitivities=[self.sensitivity]
            )
            logging.info("Initialized Porcupine with the provided keyword model.")
        except Exception as e:
            logging.error(f"Failed to initialize Porcupine: {e}")
            raise

        # Initialize PyAudio
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            logging.error(f"Failed to initialize PyAudio: {e}")
            raise

    def start_detection(self):
        """
        Starts the wake word detection process in a separate thread.
        """
        logging.info("Starting wake word detection...")
        self.running = True
        Thread(target=self._detect_wake_word, daemon=True).start()

    def _detect_wake_word(self):
        """
        Internal method that continuously listens for the wake word.
        """
        try:
            self.stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            logging.info("Audio stream opened successfully.")

            while self.running:
                try:
                    pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                    # Process audio frame with Porcupine
                    result = self.porcupine.process(pcm)
                    if result >= 0:
                        logging.info("Wake word detected!")
                        self.on_wake_word_detected()
                except Exception as e:
                    logging.error(f"Error during audio processing: {e}")

        except Exception as e:
            logging.error(f"Failed to start audio stream: {e}")
            self.stop_detection()

    def on_wake_word_detected(self):
        """
        Callback triggered when the wake word is detected.
        Override this method to define custom behavior.
        """
        logging.info("Wake word callback invoked. Override 'on_wake_word_detected' for custom behavior.")
        print("Wake word detected! Performing the next action...")

    def stop_detection(self):
        """
        Stops the wake word detection process.
        """
        logging.info("Stopping wake word detection...")
        self.running = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            logging.info("Audio stream closed.")

        if self.porcupine:
            self.porcupine.delete()
            logging.info("Porcupine resources released.")

        if self.audio:
            self.audio.terminate()
            logging.info("PyAudio resources terminated.")


if __name__ == "__main__":
    # Example usage
    model_path = "path/to/Hey-Devin_en_windows_v3_0_0.ppn"  # Replace with your actual keyword model path
    access_key = "YOUR_ACCESS_KEY_HERE"  # Replace with your actual access key

    try:
        detector = WakeWordDetector(keyword_model_path=model_path, access_key=access_key)
        detector.start_detection()
        print("Listening for 'Hey Devin'... Press Ctrl+C to stop.")

        # Keep the script running
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping wake word detection...")
        detector.stop_detection()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"Error: {e}")
