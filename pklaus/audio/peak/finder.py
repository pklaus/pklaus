"""
source: https://www.swharden.com/wp/2016-07-19-realtime-audio-visualization-in-python/
"""

import soundcard as sc
import numpy as np
import matplotlib.pyplot as plt

def find_peak(data, fs=48000):
    data = data * np.hanning(len(data)) # smooth the FFT by windowing data
    fft = abs(np.fft.rfft(data))
    freq = np.fft.rfftfreq(len(data), 1.0/fs)
    return freq[np.where(fft==np.max(fft))[0][0]]+1

def main():
    CHUNK = 8192 # number of data points to read at a time
    RATE = 48000 # time resolution of the recording device (Hz)
    default_mic = sc.default_microphone()

    try:
        with default_mic.recorder(RATE, channels=1, blocksize=CHUNK//16) as rec:
            while True:
                data = rec.record(numframes=CHUNK)
                data = data.reshape((len(data)))
                peak_f = find_peak(data, fs=RATE)
                print("peak frequency: %d Hz" % peak_f)
    except KeyboardInterrupt:
        print()

if __name__ == "__main__":
    main()
