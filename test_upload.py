import requests

import wave

# Create a valid test audio file
filename = "test_audio.wav"
with wave.open(filename, 'wb') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 2 bytes per sample
    wav_file.setframerate(44100)
    # Write 1 second of silence
    wav_file.writeframes(b'\x00' * 44100 * 2)

# Upload the file
with open(filename, "rb") as f:
    files = {"file": (filename, f, "audio/wav")}
    response = requests.post("http://127.0.0.1:8000/analyze", files=files)

# Print the response
print("Status Code:", response.status_code)
print("\nJSON Response:")
print(response.json())
print("\nFormatted JSON:")
import json
print(json.dumps(response.json(), indent=2))
