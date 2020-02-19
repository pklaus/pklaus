"""
source: https://gist.github.com/boylea/1a0b5442171f9afbf372
"""

import numpy as np
import pyqtgraph as pg
import soundcard as sc
from PyQt5 import QtCore, QtGui
import threading
import atexit
import time

FS = 48000 #Hz
CHUNKSZ = 8192 #samples

class MicrophoneRecorder():
    def __init__(self, signal, rate=48000, chunksize=2048):
        self.signal = signal
        self.rate = rate
        self.chunksize = chunksize
        self.mic = sc.default_microphone()
        self.lock = threading.Lock()
        self.stop = False
        self.frames = []
        self.t = threading.Thread(target=self.capture_frames, daemon=True)
        atexit.register(self.close)
        self.start()

    def capture_frames(self):
        try:
            with self.mic.recorder(self.rate, channels=1, blocksize=self.chunksize//16) as rec:
                while True:
                    data = rec.record(numframes=self.chunksize)
                    data = data.reshape((len(data)))
                    with self.lock:
                        self.frames.append(data)
                    if self.stop:
                        break
        except KeyboardInterrupt:
            pass

    def read(self):
        while(len(self.frames) == 0):
            time.sleep(0.01)
        with self.lock:
            data = self.frames[0]
            del self.frames[0]
            y = (np.rint(data*(2**15-1))).astype('int16')
            self.signal.emit(y)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def start(self):
       self.t.start()

    def close(self):
       with self.lock:
           self.stop = True
       self.t.join()

class SpectrogramWidget(pg.PlotWidget):
    read_collected = QtCore.pyqtSignal(np.ndarray)
    def __init__(self):
        super(SpectrogramWidget, self).__init__()

        self.img = pg.ImageItem()
        self.addItem(self.img)

        self.img_array = np.zeros((1000, CHUNKSZ//2+1))

        # bipolar colormap
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)

        # set colormap
        self.img.setLookupTable(lut)
        self.img.setLevels([-50,40])

        # setup the correct scaling for y-axis
        freq = np.arange((CHUNKSZ/2)+1)/(float(CHUNKSZ)/FS)
        yscale = 1.0/(self.img_array.shape[1]/freq[-1])
        self.img.scale((1./FS)*CHUNKSZ, yscale)

        self.setLabel('left', 'Frequency', units='Hz')

        # prepare window for later use
        self.win = np.hanning(CHUNKSZ)
        self.show()

    def update(self, chunk):
        # normalized, windowed frequencies in data chunk
        spec = np.fft.rfft(chunk*self.win) / CHUNKSZ
        # get magnitude 
        psd = abs(spec)
        # convert to dB scale
        psd = 20 * np.log10(psd)

        # roll down one and replace leading edge with new data
        self.img_array = np.roll(self.img_array, -1, 0)
        self.img_array[-1:] = psd

        self.img.setImage(self.img_array, autoLevels=False)

def main():
    app = QtGui.QApplication([])
    w = SpectrogramWidget()
    w.read_collected.connect(w.update)

    mic = MicrophoneRecorder(w.read_collected, rate=FS, chunksize=CHUNKSZ)

    # time (seconds) between reads
    interval = FS/CHUNKSZ
    t = QtCore.QTimer()
    t.timeout.connect(mic.read)
    t.start(1000/interval) #QTimer takes ms

    app.exec_()
    mic.close()

if __name__ == '__main__':
    main()
