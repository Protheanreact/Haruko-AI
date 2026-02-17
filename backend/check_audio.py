import pyaudio

p = pyaudio.PyAudio()
print("Verfügbare Audio-Geräte am Server:")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"\nIndex {i}: {info['name']}")
        print(f"  Eingänge: {info['maxInputChannels']}")
        print(f"  Standard Rate: {info['defaultSampleRate']}")
        try:
            test_stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=i, frames_per_buffer=1024)
            test_stream.close()
            print("  [OK] 16000Hz unterstützt.")
        except Exception as e:
            print(f"  [FEHLER] 16000Hz nicht unterstützt: {e}")
p.terminate()
