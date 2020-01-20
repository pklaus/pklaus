#!/usr/bin/env python

"""
Idea and some code from
https://www.swharden.com/wp/2016-07-19-realtime-audio-visualization-in-python/

pip install numpy pyaudio
"""

import pyaudio
import numpy as np

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bars', '-b', type=int)
    args = parser.parse_args()

    maxValue = 2**16
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,channels=2,rate=44100,
                    input=True, frames_per_buffer=1024)

    try:
        while True:
            data = np.frombuffer(stream.read(1024),dtype=np.int16)
            dataL = data[0::2]
            dataR = data[1::2]
            peakL = np.abs(np.max(dataL).astype(np.int64)-np.min(dataL))/maxValue
            peakR = np.abs(np.max(dataR).astype(np.int64)-np.min(dataR))/maxValue
            if args.bars:
                bars = args.bars
                lString = "#"*int(peakL*bars)+"-"*int(bars-peakL*bars)
                rString = "#"*int(peakR*bars)+"-"*int(bars-peakR*bars)
                print("L=[%s]\tR=[%s]"%(lString, rString))
            else:
                print("L:%00.02f R:%00.02f"%(peakL*100, peakR*100))
    except KeyboardInterrupt:
        print()

if __name__ == "__main__":
    main()
