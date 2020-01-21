"""
https://flothesof.github.io/pyqt-microphone-fft-application.html
https://github.com/flothesof/LiveFFTPitchTracker/blob/master/LiveFFT.py
"""

import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt

import pyaudio

import threading
import atexit
import math

sample_style = (pyaudio.paFloat32, np.float32, 1.0, -24, 24)
#sample_style = (pyaudio.paInt16, np.int16, 32768, -24, 24)

class DecibelSlider(QtWidgets.QSlider):

    """
    inspired by
    https://www.qtcentre.org/threads/67835-Slider-with-log-ticks?p=298369#post298369
    """

    INT_MIN = 0
    INT_MAX = 1000000

    def __init__(self, low_db=-60, high_db=6):
        super(DecibelSlider, self).__init__(Qt.Horizontal)
        self.setMinimum(self.INT_MIN)
        self.setMaximum(self.INT_MAX)
        self.low_db = low_db
        self.high_db = high_db
        self.lowest_as_inf = False

    @classmethod
    def db_to_power_ratio(cls, db):
        return 10**(db/10)

    @classmethod
    def db_to_amplitude_ratio(cls, db):
        return 10**(db/20)

    def power_ratio(self):
        return self.db_to_power_ratio(self.decibel())

    def amplitude_ratio(self):
        return self.db_to_amplitude_ratio(self.decibel())

    def set_power_ratio(self, pr):
        db = 10 * math.log10(pr)
        self.set_decibel(db)

    def set_amplitude_ratio(self, ar):
        db = 20 * math.log10(ar)
        self.set_decibel(db)

    def set_decibel(self, db):
        value = min(self.INT_MAX, max(self.INT_MIN, self.db_to_int(db)))
        self.setValue(round(value))

    def decibel(self):
        return self.int_to_db(self.value())

    def db_to_int(self, db):
        return (db - self.low_db) \
             * (self.INT_MAX - self.INT_MIN) \
             / (self.high_db - self.low_db)

    def int_to_db(self, val):
        return (val - self.INT_MIN) \
             * (self.high_db - self.low_db) \
             / (self.INT_MAX - self.INT_MIN) + self.low_db

    def paintEvent(self, event):
        """Paint log scale ticks"""
        super(DecibelSlider, self).paintEvent(event)
        qp = QtGui.QPainter(self)
        pen = QtGui.QPen()
        pen.setWidth(2)
        pen.setColor(Qt.black)

        qp.setPen(pen)
        font = QtGui.QFont('Times', 10)
        font_x_offset = font.pointSize()/2
        qp.setFont(font)
        size = self.size()
        contents = self.contentsRect()
        #db_val_list = [40, 20, 10, 6, 3, 0, -3, -6, -10, -20, -40, -60]
        db_val_list = list(range(self.low_db, math.ceil(self.high_db+0.001), 6))
        for val in db_val_list:
            range_padding = 10 # padding of contents.width() on left and right side
            db_as_int = self.db_to_int(val)
            x_val = db_as_int \
                    * (contents.width() - 2*range_padding) \
                    / (self.INT_MAX - self.INT_MIN) \
                    + range_padding
            if val == min(db_val_list) and self.lowest_as_inf:
                qp.drawText(round(x_val + font_x_offset),
                            round(contents.y() + font.pointSize()),
                            '-oo')
            elif val == max(db_val_list):
                # right align last value
                qp.drawText(round(x_val - font_x_offset - 100),
                            round(contents.y() + font.pointSize() - QtGui.QFontMetricsF(font).ascent()),
                            100,
                            round(font.pointSize() * 5),
                            int(Qt.AlignRight | Qt.AlignTop),
                            #Qt.AlignRight,
                            '{0:2}'.format(val))
            else:
                qp.drawText(round(x_val + font_x_offset),
                            round(contents.y() + font.pointSize()),
                            '{0:2}'.format(val))
            qp.drawLine(round(x_val),
                        round(contents.y() - font.pointSize()),
                        round(x_val),
                        round(contents.y() + contents.height()))

class MicrophoneRecorder(object):
    # class taken from the SciPy 2015 Vispy talk opening example
    # see https://github.com/vispy/vispy/pull/928
    def __init__(self, rate=4000, chunksize=1024):
        self.rate = rate
        self.chunksize = chunksize
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=sample_style[0],
                                  channels=1,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.chunksize,
                                  stream_callback=self.new_frame)
        self.lock = threading.Lock()
        self.stop = False
        self.frames = []
        atexit.register(self.close)

    def new_frame(self, data, frame_count, time_info, status):
        data = np.frombuffer(data, sample_style[1])
        with self.lock:
            self.frames.append(data)
            if self.stop:
                return None, pyaudio.paComplete
        return None, pyaudio.paContinue

    def get_frames(self):
        with self.lock:
            frames = self.frames
            self.frames = []
            return frames

    def start(self):
        self.stream.start_stream()

    def close(self):
        with self.lock:
            self.stop = True
        self.stream.close()
        self.p.terminate()

class MplFigure(object):
    def __init__(self, parent):
        self.figure = Figure(facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, parent)

class LiveFFTWidget(QtWidgets.QWidget):

    chunksize = 1024*8
    rate = 48000
    #chunksize = 1024
    #rate = 4000

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        # customize the UI
        self.initUI()

        # init class data
        self.initData()

        # connect slots
        self.connectSlots()

        # init MPL widget
        self.initMplWidget()

    def initUI(self):

        hbox_autogain = QtWidgets.QHBoxLayout()
        autoGain = QtWidgets.QLabel('Auto gain for frequency spectrum')
        autoGainCheckBox = QtWidgets.QCheckBox(checked=True)
        hbox_autogain.addWidget(autoGain)
        hbox_autogain.addWidget(autoGainCheckBox)

        # reference to checkbox
        self.autoGainCheckBox = autoGainCheckBox

        hbox_fixedGain = QtWidgets.QHBoxLayout()
        fixedGain = QtWidgets.QLabel('Manual gain level for frequency spectrum:')
        fixedGainVal = QtWidgets.QLabel()
        fixedGainSlider = DecibelSlider(low_db=sample_style[3], high_db=sample_style[4])
        def fixedGainSliderChanged():
            fixedGainVal.setText(f"{fixedGainSlider.decibel():6.1f} dB")
        fixedGainSlider.valueChanged.connect(fixedGainSliderChanged)
        fixedGainSliderChanged()
        hbox_fixedGain.addWidget(fixedGain)
        hbox_fixedGain.addWidget(fixedGainVal)
        hbox_fixedGain.addWidget(fixedGainSlider)

        self.fixedGainSlider = fixedGainSlider

        hbox_cutoff = QtWidgets.QHBoxLayout()
        cutoff = QtWidgets.QLabel('Cutoff lowest frequencies (improves autoscaling for high frequencies):')
        cutoffVal = QtWidgets.QLabel()
        cutoffSlider = QtWidgets.QSlider(Qt.Horizontal)
        cutoffSlider.setMaximum(self.chunksize//2)
        cutoffSlider.setValue(1)
        def cutoffSliderChanged():
            cutoffVal.setText(f"{cutoffSlider.value()} Hz")
        cutoffSlider.valueChanged.connect(cutoffSliderChanged)
        cutoffSliderChanged()
        hbox_cutoff.addWidget(cutoff)
        hbox_cutoff.addWidget(cutoffVal)
        hbox_cutoff.addWidget(cutoffSlider)

        self.cutoffSlider = cutoffSlider

        vbox = QtWidgets.QVBoxLayout()

        vbox.addLayout(hbox_autogain)
        vbox.addLayout(hbox_fixedGain)
        vbox.addLayout(hbox_cutoff)

        # mpl figure
        self.main_figure = MplFigure(self)
        vbox.addWidget(self.main_figure.toolbar)
        vbox.addWidget(self.main_figure.canvas)

        self.setLayout(vbox)

        self.setGeometry(10, 10, 900, 900)
        self.setWindowTitle('LiveFFT')
        self.show()
        # timer for callbacks, taken from:
        # http://ralsina.me/weblog/posts/BB974.html
        timer = QtCore.QTimer()
        timer.timeout.connect(self.handleNewData)
        timer.start(100)
        # keep reference to timer
        self.timer = timer


    def initData(self):
        mic = MicrophoneRecorder(rate=self.rate, chunksize=self.chunksize)
        mic.start()

        # keeps reference to mic
        self.mic = mic

        # computes the parameters that will be used during plotting
        self.freq_vect = np.fft.rfftfreq(mic.chunksize,
                                         1./mic.rate)
        self.time_vect = np.arange(mic.chunksize, dtype=sample_style[1]) / mic.rate * 1000

    def connectSlots(self):
        pass

    def initMplWidget(self):
        """creates initial matplotlib plots in the main window and keeps
        references for further use"""
        # top plot
        self.ax_top = self.main_figure.figure.add_subplot(211)
        self.ax_top.set_ylim(-sample_style[2], sample_style[2])
        self.ax_top.set_xlim(0, self.time_vect.max())
        self.ax_top.set_xlabel(u'time (ms)', fontsize=6)

        # bottom plot
        self.ax_bottom = self.main_figure.figure.add_subplot(212)
        self.ax_bottom.set_ylim(0, sample_style[2])
        self.ax_bottom.set_xlim(0, self.freq_vect.max())
        self.ax_bottom.set_xlabel(u'frequency (Hz)', fontsize=6)
        # line objects
        self.line_top, = self.ax_top.plot(self.time_vect,
                                         np.ones_like(self.time_vect))

        self.line_bottom, = self.ax_bottom.plot(self.freq_vect,
                                               np.ones_like(self.freq_vect))



    def handleNewData(self):
        """ handles the asynchroneously collected sound chunks """
        # gets the latest frames
        frames = self.mic.get_frames()

        if len(frames) > 0:
            # keeps only the last frame
            current_frame = frames[-1]
            # plots the time signal
            self.line_top.set_data(self.time_vect, current_frame)
            # computes and plots the fft signal
            fft_frame = np.fft.rfft(current_frame)
            fft_frame[0:self.cutoffSlider.value()] = 0.0
            if self.autoGainCheckBox.checkState() == QtCore.Qt.Checked:
                gain = 1/np.abs(fft_frame).max()*sample_style[2]
                self.fixedGainSlider.set_power_ratio(gain)
            else:
                gain = self.fixedGainSlider.power_ratio()
            fft_frame *= gain
            self.line_bottom.set_data(self.freq_vect, np.abs(fft_frame))

            # refreshes the plots
            self.main_figure.canvas.draw()

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = LiveFFTWidget()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
