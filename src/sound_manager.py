import os
from PySide6.QtCore import QUrl, QObject, Signal
from PySide6.QtMultimedia import QSoundEffect
from src.utils import get_resource_path

class SoundManager(QObject):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.effect = QSoundEffect()
        self.is_playing = False

    def play_alert_sound(self, priority="critical"):
        if not self.config.get("audio_enabled", True):
            return

        sound_files = self.config.get("sound_files", {})
        sound_rel_path = sound_files.get(priority.lower(), "sounds/siren.wav")
        
        abs_path = get_resource_path(sound_rel_path)
        if not os.path.exists(abs_path):
            abs_path = get_resource_path("sounds/siren.wav")

        if not os.path.exists(abs_path):
            print(f"[SoundManager Warning] Audio file not found at: {abs_path}")
            return

        self.stop_sound()

        try:
            self.effect.setSource(QUrl.fromLocalFile(abs_path))
            
            # Set loop count based on config & priority
            loop = self.config.get("audio_loop", True)
            if priority in ("critical", "disaster") and loop:
                self.effect.setLoopCount(QSoundEffect.Loop.Infinite.value)
            else:
                self.effect.setLoopCount(1)

            self.effect.setVolume(1.0)
            self.effect.play()
            self.is_playing = True
            print(f"[SoundManager] Playing sound '{abs_path}' for priority '{priority}'")
        except Exception as e:
            print(f"[SoundManager Error] Failed to play sound: {e}")

    def stop_sound(self):
        if self.effect and self.effect.isPlaying():
            self.effect.stop()
        self.is_playing = False
