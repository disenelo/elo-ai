"""
plugins/voice/plugin.py — Voice I/O plugin.

Handles speech-to-text input and text-to-speech output.
Does NOT generate responses — delegates to the active text plugin.

For response generation, voice passes audio through STT first, then the result
goes to whatever text plugin is active. The voice plugin handles the I/O layer only.

Capabilities: voice_input, voice_output

Future integrations:
    STT: Whisper (local) or Deepgram/AssemblyAI (API)
    TTS: pyttsx3 (local), ElevenLabs (API), Coqui TTS (local)

Environment:
    ELO_VOICE_STT_ENGINE   "whisper" | "deepgram" | "stdin" (default)
    ELO_VOICE_TTS_ENGINE   "pyttsx3" | "elevenlabs" | "print" (default)
"""

import logging
from plugins.base import PluginBase

logger = logging.getLogger(__name__)


class VoicePlugin(PluginBase):

    NAME         = "voice"
    VERSION      = "0.1"
    CAPABILITIES = ["voice_input", "voice_output"]

    def is_available(self) -> bool:
        # Available in stub/print mode always.
        # Return True when STT/TTS hardware or API is confirmed present.
        return False   # set True once STT/TTS is wired

    def generate_response(self, user_input: str, context: dict) -> str:
        # Voice plugin does not generate — it delegates to the active text plugin.
        # Call capture_input() → pass to registry.generate_response() → deliver_output()
        from core.behavior_engine import generate_offline_response
        return generate_offline_response(
            user_input,
            context.get("memory", {}),
            context.get("mode", "companion"),
        )

    def capture_input(self) -> str:
        """
        Capture audio and return transcribed text.

        HARDWARE HOOK — replace with Whisper:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            return result["text"].strip()
        """
        logger.info("VoicePlugin: capture_input() stub — no STT engine wired.")
        return ""

    def deliver_output(self, response: str, context: dict):
        """
        Speak the response using TTS.

        HARDWARE HOOK — replace with pyttsx3:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(response)
            engine.runAndWait()
        """
        logger.info("VoicePlugin: deliver_output() stub — no TTS engine wired.")
        print(f"[VOICE OUTPUT] {response}")

    def on_load(self):
        logger.info("VoicePlugin loaded — STT/TTS hooks available, engines not yet wired.")
