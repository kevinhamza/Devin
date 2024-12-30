"""
AI Integration: ChatGPT Connector
Description: This module integrates the Devin project with the ChatGPT API for advanced conversational capabilities and task execution.
"""

import os
import requests
from typing import Dict, Optional, List

class ChatGPTConnector:
    """
    A connector class to interact with the ChatGPT API for generating text responses, executing commands,
    and enabling conversational AI within the Devin framework.
    """

    def __init__(self, api_key: str, api_url: str = "https://api.openai.com/v1/chat/completions"):
        """
        Initializes the ChatGPT connector with the API key and endpoint.
        """
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def send_message(self, messages: List[Dict[str, str]], max_tokens: int = 1500, temperature: float = 0.7) -> Optional[Dict]:
        """
        Sends a message to the ChatGPT API and returns the response.

        :param messages: A list of messages for the conversation context.
        :param max_tokens: Maximum tokens for the response.
        :param temperature: Sampling temperature for response creativity.
        :return: The API response as a dictionary.
        """
        payload = {
            "model": "gpt-4",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with ChatGPT API: {e}")
            return None

    def extract_response_text(self, api_response: Dict) -> Optional[str]:
        """
        Extracts the generated text from the ChatGPT API response.

        :param api_response: The raw response from the ChatGPT API.
        :return: The generated text or None if unavailable.
        """
        try:
            return api_response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            print("Error parsing API response.")
            return None

    def execute_task(self, prompt: str) -> Optional[str]:
        """
        Executes a specific task based on the given prompt.

        :param prompt: The task description or user query.
        :return: The response or execution result.
        """
        messages = [{"role": "system", "content": "You are a highly intelligent assistant."},
                    {"role": "user", "content": prompt}]

        response = self.send_message(messages)
        if response:
            return self.extract_response_text(response)
        return None

# Example Usage
if __name__ == "__main__":
    # Set API key
    api_key = os.getenv("CHATGPT_API_KEY", "your_api_key_here")
    connector = ChatGPTConnector(api_key)

    # Sample prompt
    prompt = "Write a Python function to calculate the factorial of a number."
    result = connector.execute_task(prompt)

    if result:
        print("ChatGPT Response:")
        print(result)
    else:
        print("Failed to fetch a response from ChatGPT.")
