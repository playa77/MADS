# v3.0.0 - Work Package 3: Async Workers
import os
import traceback
from PyQt6.QtCore import QRunnable, pyqtSignal, QObject
from openai import OpenAI

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    started = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(str) # Full response text
    token_received = pyqtSignal(str) # Streaming token

class OpenRouterWorker(QRunnable):
    """
    Worker thread for making blocking API calls to OpenRouter.
    """
    def __init__(self, api_key: str, model_name: str, messages: list, temperature: float = 0.7):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        self.messages = messages
        self.temperature = temperature
        self.signals = WorkerSignals()
        self.base_url = "https://openrouter.ai/api/v1"

    def run(self):
        self.signals.started.emit()
        try:
            client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )

            # We use streaming to make the UI feel responsive
            stream = client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
                temperature=self.temperature,
                stream=True,
                extra_headers={
                    "HTTP-Referer": "https://github.com/multi-agent-debate",
                    "X-Title": "DebatePlatformV3"
                }
            )

            full_content = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    full_content += token
                    self.signals.token_received.emit(token)
            
            self.signals.result.emit(full_content)

        except Exception as e:
            error_msg = "".join(traceback.format_exception(None, e, e.__traceback__))
            self.signals.error.emit(error_msg)
        finally:
            self.signals.finished.emit()
