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
        try:
            import voice.stt as _stt
            return _stt.is_available()
        except Exception:
            return False

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
        try:
            import voice.stt as _stt
            return _stt.capture()
        except Exception as e:
            logger.info("VoicePlugin: capture_input() error: %s", e)
            return ""

    def deliver_output(self, response: str, context: dict):
        snap = {
            "emotion": context.get("emotional_state", "neutral"),
            "tone":    context.get("tone", "DIRECT"),
            "pacing":  context.get("voice_pacing", "measured"),
            "warmth":  context.get("voice_warmth", 0.7),
        }
        try:
            import plugins.voice.tts_output as _tts
            _tts.speak(response, emotion_snapshot=snap)
        except Exception as e:
            logger.warning("VoicePlugin: deliver_output() TTS error: %s", e)
            print(f"[VOICE OUTPUT] {response}")

    def on_load(self):
        logger.info("VoicePlugin loaded — STT/TTS hooks available, engines not yet wired.")
