import os
import math
import struct
import wave

def generate_wav(filepath, duration_sec, sample_rate=44100, waveform_fn=None):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    num_samples = int(sample_rate * duration_sec)
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = []
        for i in range(num_samples):
            t = i / sample_rate
            sample_val = waveform_fn(t, duration_sec)
            # Clip to [-1.0, 1.0]
            sample_val = max(-1.0, min(1.0, sample_val))
            # Convert to 16-bit signed integer
            packed_sample = struct.pack('<h', int(sample_val * 32767))
            frames.append(packed_sample)
            
        wav_file.writeframes(b''.join(frames))
    print(f"Generated sound: {filepath}")

def wave_gentle_chime(t, duration):
    """
    Super elegant, soft glass chime (C5 - G5 - C6 chord with soft attack & exponential decay).
    Sounds like a high-end luxury app notification sound.
    """
    attack = min(1.0, t / 0.008)
    decay = math.exp(-4.2 * t)
    env = attack * decay

    f1, f2, f3, f4 = 523.25, 783.99, 1046.50, 1318.51
    tone = (
        0.45 * math.sin(2 * math.pi * f1 * t) +
        0.30 * math.sin(2 * math.pi * f2 * t) +
        0.20 * math.sin(2 * math.pi * f3 * t) +
        0.10 * math.sin(2 * math.pi * f4 * t)
    )
    return 0.5 * tone * env

def wave_gentle_alert(t, duration):
    """
    Two-tone polite alert (Arpeggio: A5 -> E6 with glass bell shimmer).
    Used for urgent messages.
    """
    attack = min(1.0, t / 0.005)
    
    if t < 0.18:
        freq = 880.0
        env = attack * math.exp(-5.0 * t)
    else:
        freq = 1318.51
        t2 = t - 0.18
        env = min(1.0, t2 / 0.005) * math.exp(-3.5 * t2)

    tone = (
        0.50 * math.sin(2 * math.pi * freq * t) +
        0.25 * math.sin(2 * math.pi * (freq * 2.0) * t) +
        0.10 * math.sin(2 * math.pi * (freq * 3.0) * t)
    )
    return 0.45 * tone * env

def generate_all_sounds(target_dir="sounds"):
    os.makedirs(target_dir, exist_ok=True)
    # Generate main elegant sounds
    generate_wav(os.path.join(target_dir, "gentle_chime.wav"), duration_sec=1.5, waveform_fn=wave_gentle_chime)
    generate_wav(os.path.join(target_dir, "gentle_alert.wav"), duration_sec=1.8, waveform_fn=wave_gentle_alert)

    # Alias all sound files to gentle versions for consistency
    generate_wav(os.path.join(target_dir, "ding.wav"), duration_sec=1.5, waveform_fn=wave_gentle_chime)
    generate_wav(os.path.join(target_dir, "warning.wav"), duration_sec=1.8, waveform_fn=wave_gentle_alert)
    generate_wav(os.path.join(target_dir, "siren.wav"), duration_sec=1.8, waveform_fn=wave_gentle_alert)
    generate_wav(os.path.join(target_dir, "airraid.wav"), duration_sec=1.8, waveform_fn=wave_gentle_alert)

if __name__ == "__main__":
    generate_all_sounds()

