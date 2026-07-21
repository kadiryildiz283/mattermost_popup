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

def wave_ding(t, duration):
    # Soft decaying sine wave ping (880Hz -> A5)
    freq = 880
    decay = math.exp(-4 * t)
    return 0.7 * math.sin(2 * math.pi * freq * t) * decay

def wave_warning(t, duration):
    # Two-tone warning beep (600Hz / 850Hz alternating every 0.25s)
    freq = 600 if int(t * 4) % 2 == 0 else 850
    return 0.8 * math.sin(2 * math.pi * freq * t)

def wave_siren(t, duration):
    # Sweeping siren (600Hz to 1200Hz back and forth)
    cycle = (math.sin(2 * math.pi * 1.5 * t) + 1) / 2  # 0 to 1
    freq = 600 + cycle * 600
    return 0.85 * math.sin(2 * math.pi * freq * t)

def wave_airraid(t, duration):
    # Heavy low oscillating air-raid siren (300Hz to 800Hz with sub-bass layer)
    sweep = 300 + 500 * (math.sin(2 * math.pi * 0.8 * t) + 1) / 2
    tone1 = math.sin(2 * math.pi * sweep * t)
    tone2 = math.sin(2 * math.pi * (sweep * 0.5) * t)  # Sub octave
    # Add pulse modulation
    pulse = 0.8 + 0.2 * math.sin(2 * math.pi * 8 * t)
    return 0.9 * ((tone1 * 0.7 + tone2 * 0.3) * pulse)

def generate_all_sounds(target_dir="sounds"):
    os.makedirs(target_dir, exist_ok=True)
    generate_wav(os.path.join(target_dir, "ding.wav"), duration_sec=1.0, waveform_fn=wave_ding)
    generate_wav(os.path.join(target_dir, "warning.wav"), duration_sec=2.0, waveform_fn=wave_warning)
    generate_wav(os.path.join(target_dir, "siren.wav"), duration_sec=2.0, waveform_fn=wave_siren)
    generate_wav(os.path.join(target_dir, "airraid.wav"), duration_sec=3.0, waveform_fn=wave_airraid)

if __name__ == "__main__":
    generate_all_sounds()
