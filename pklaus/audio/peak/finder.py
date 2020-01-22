"""
source: https://www.swharden.com/wp/2016-07-19-realtime-audio-visualization-in-python/
"""

import pyaudio
import numpy as np
import matplotlib.pyplot as plt

def find_peak(data, fs=48000):
    data = data * np.hanning(len(data)) # smooth the FFT by windowing data
    fft = abs(np.fft.rfft(data))
    fft = fft[:int(len(fft)/2)] # keep only first half
    freq = np.fft.rfftfreq(len(data), 1.0/fs)
    freq = freq[:int(len(freq)/2)] # keep only first half
    return freq[np.where(fft==np.max(fft))[0][0]]+1

def main():
    CHUNK = 8192 # number of data points to read at a time
    RATE = 48000 # time resolution of the recording device (Hz)
    p=pyaudio.PyAudio() # start the PyAudio class
    stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
                  frames_per_buffer=CHUNK) #uses default input device
    try:
        while True:
            data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
            peak_f = find_peak(data, fs=RATE)
            print("peak frequency: %d Hz" % peak_f)
    except:
        print()
    finally:
        # close the stream gracefully
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
