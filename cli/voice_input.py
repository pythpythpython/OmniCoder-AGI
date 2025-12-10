#!/usr/bin/env python3
"""
Voice Input Module for OmniCoder-AGI CLI

Provides voice input support for hands-free operation.
"""

from __future__ import annotations

import sys
import threading
import queue
from typing import Optional, Callable

# Try to import speech recognition
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

class VoiceInput:
    """Voice input handler for CLI."""
    
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self.is_listening = False
        self._callback: Optional[Callable[[str], None]] = None
        self._queue: queue.Queue = queue.Queue()
        
        if SPEECH_AVAILABLE:
            self.recognizer = sr.Recognizer()
    
    def is_available(self) -> bool:
        """Check if voice input is available."""
        return SPEECH_AVAILABLE
    
    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """Start listening for voice input."""
        if not SPEECH_AVAILABLE:
            print("⚠️  Voice input not available. Install SpeechRecognition and pyaudio.")
            return
        
        self._callback = callback
        self.is_listening = True
        
        print("🎤 Listening for voice input... (say 'stop' to end)")
        
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()
    
    def stop_listening(self):
        """Stop listening for voice input."""
        self.is_listening = False
        print("🎤 Voice input stopped.")
    
    def _listen_loop(self):
        """Main listening loop."""
        with sr.Microphone() as source:
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=30)
                    text = self._recognize(audio)
                    
                    if text:
                        if text.lower() == "stop":
                            self.stop_listening()
                            break
                        
                        print(f"🎤 Heard: {text}")
                        
                        if self._callback:
                            self._callback(text)
                        else:
                            self._queue.put(text)
                
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    print(f"⚠️  Voice error: {e}")
    
    def _recognize(self, audio) -> Optional[str]:
        """Recognize speech from audio."""
        try:
            # Try Google Speech Recognition (free, no API key needed)
            return self.recognizer.recognize_google(audio)
        except sr.RequestError:
            # Try Sphinx (offline, less accurate)
            try:
                return self.recognizer.recognize_sphinx(audio)
            except:
                return None
        except sr.UnknownValueError:
            return None
    
    def get_input(self, timeout: float = 30) -> Optional[str]:
        """Get voice input synchronously."""
        if not SPEECH_AVAILABLE:
            print("⚠️  Voice input not available.")
            return None
        
        print("🎤 Speak your command...")
        
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=30)
                text = self._recognize(audio)
                
                if text:
                    print(f"🎤 Heard: {text}")
                    return text
                else:
                    print("⚠️  Could not understand audio.")
                    return None
            
            except sr.WaitTimeoutError:
                print("⚠️  Voice input timed out.")
                return None
            except Exception as e:
                print(f"⚠️  Voice error: {e}")
                return None
    
    def transcribe_file(self, audio_file: str) -> Optional[str]:
        """Transcribe an audio file."""
        if not SPEECH_AVAILABLE:
            return None
        
        try:
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
                return self._recognize(audio)
        except Exception as e:
            print(f"⚠️  Transcription error: {e}")
            return None


class VoiceCLI:
    """Voice-enabled CLI wrapper."""
    
    def __init__(self, handler: Callable[[str], None]):
        self.handler = handler
        self.voice = VoiceInput()
    
    def run_voice_mode(self):
        """Run CLI in voice mode."""
        if not self.voice.is_available():
            print("❌ Voice input not available. Install: pip install SpeechRecognition pyaudio")
            return
        
        print("=" * 60)
        print("  OmniCoder-AGI Voice Mode")
        print("=" * 60)
        print()
        print("Commands:")
        print("  - Say your task naturally")
        print("  - Say 'run [task]' to execute a task")
        print("  - Say 'train' to start training")
        print("  - Say 'upgrade' to run self-upgrade")
        print("  - Say 'stats' to show statistics")
        print("  - Say 'stop' or 'exit' to quit")
        print()
        
        self.voice.start_listening(callback=self._process_voice_command)
        
        # Wait for stop
        try:
            while self.voice.is_listening:
                pass
        except KeyboardInterrupt:
            self.voice.stop_listening()
    
    def _process_voice_command(self, text: str):
        """Process a voice command."""
        text_lower = text.lower()
        
        # Check for exit commands
        if text_lower in ["stop", "exit", "quit", "bye"]:
            self.voice.stop_listening()
            return
        
        # Parse and execute command
        if text_lower.startswith("run "):
            task = text[4:]
            self.handler(f"run \"{task}\"")
        elif text_lower == "train":
            self.handler("train --intensity high")
        elif text_lower == "upgrade":
            self.handler("upgrade --auto")
        elif text_lower == "stats":
            self.handler("stats")
        elif text_lower == "boards":
            self.handler("boards")
        elif text_lower == "engines":
            self.handler("engines")
        elif text_lower == "help":
            self.handler("--help")
        else:
            # Treat as a task
            self.handler(f"run \"{text}\"")


def add_voice_commands(parser):
    """Add voice-related commands to argument parser."""
    # Add to main parser
    parser.add_argument("--voice", action="store_true", help="Enable voice input mode")
    
    return parser


# Standalone test
if __name__ == "__main__":
    voice = VoiceInput()
    
    if voice.is_available():
        print("Voice input available!")
        text = voice.get_input()
        if text:
            print(f"You said: {text}")
    else:
        print("Voice input not available. Install: pip install SpeechRecognition pyaudio")
