#!/usr/bin/env python

"""
https://www.christiansteinmetz.com/projects-blog/pyloudnorm
https://github.com/csteinmetz1/pyloudnorm
pip install numpy pyaudio pyloudnorm
"""

import pyloudnorm as pyln
import pyaudio
import numpy as np

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sampling-rate', '-r', default=48000, type=int)
    args = parser.parse_args()

    rate = args.sampling_rate
    block_size = 0.4
    frames_per_buffer = int(block_size*rate)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,channels=2,rate=rate,
                    input=True, frames_per_buffer=frames_per_buffer)

    meter = pyln.Meter(rate, block_size=0.4)
    try:
        while True:
            data = np.frombuffer(stream.read(frames_per_buffer),dtype=np.float32)
            dataL = data[0::2]
            dataR = data[1::2]
            valL = meter.integrated_loudness(dataL) # LUFS
            valR = meter.integrated_loudness(dataR)
            #if args.bars:
            #    lString = "#"*int(-valL)+"-"*int(bars+valL)
            #    rString = "#"*int(-valR)+"-"*int(bars+valR)
            #    print("L=[%s]\tR=[%s]"%(lString, rString))
            print("L:%+6.2f R:%+6.2f"%(valL, valR))
    except KeyboardInterrupt:
        print()

if __name__ == "__main__":
    main()
