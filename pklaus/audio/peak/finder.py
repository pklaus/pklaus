"""
source: https://www.swharden.com/wp/2016-07-19-realtime-audio-visualization-in-python/
"""

import pyaudio
import numpy as np
import matplotlib.pyplot as plt

np.set_printoptions(suppress=True) # don't use scientific notation

CHUNK = 8192 # number of data points to read at a time
RATE = 48000 # time resolution of the recording device (Hz)

p=pyaudio.PyAudio() # start the PyAudio class
stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
              frames_per_buffer=CHUNK) #uses default input device

# create a numpy array holding a single read of audio data
while True:
    data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
    data = data * np.hanning(len(data)) # smooth the FFT by windowing data
    fft = abs(np.fft.rfft(data))
    fft = fft[:int(len(fft)/2)] # keep only first half
    freq = np.fft.rfftfreq(CHUNK, 1.0/RATE)
    freq = freq[:int(len(freq)/2)] # keep only first half
    freqPeak = freq[np.where(fft==np.max(fft))[0][0]]+1
    print("peak frequency: %d Hz"%freqPeak)

# close the stream gracefully
stream.stop_stream()
stream.close()
p.terminate()
