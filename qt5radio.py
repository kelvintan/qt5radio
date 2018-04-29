#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
TODO
let user know what other station are playing right now. the website tinein could be of help here. https://tunein.com/
"""

from PyQt5.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton,
                             QHBoxLayout, QVBoxLayout,
                             QPlainTextEdit, QApplication, QSlider,
                             QToolTip)
from PyQt5.QtGui import (QIcon, QCursor)
from PyQt5.QtCore import (QSize, QEvent)

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

import sys
import time
import os

from stations.stations import radio_db

# Trying to find the correct icons directory depending on how you start the program
file_dir=os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(file_dir, 'icons')):
    # starting the python script in the source directory
    icons_dir=os.path.join(file_dir, 'icons')
else:
    # starting the python script in system path
    # __file__: /usr/local/lib/python3.5/dist-packages/qt5radio-0.1-py3.5.egg/EGG-INFO/scripts/qt5radio.py
    # icons_dir: /usr/local/lib/python3.5/dist-packages/qt5radio-0.1-py3.5.egg/icons
    icons_dir=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "icons")

# example of gstream that works
# reference: https://stackoverflow.com/questions/4689772/gstreamer-record-iradio-mode-artifacts
# reference https://github.com/gkralik/python-gst-tutorial/blob/master/basic-tutorial-7.py

# playing and decoding of icecast(?) stream
# gst-launch-1.0 souphttpsrc location=http://20673.live.streamtheworld.com/UFM_1003_SC iradio-mode=true ! tee name=t ! decodebin ! audioconvert ! playsink t. ! icydemux ! fakesink -t

# playing and recording
# gst-launch-1.0 souphttpsrc location=http://20673.live.streamtheworld.com/UFM_1003_SC iradio-mode=true ! decodebin ! audioconvert ! tee name=t ! playsink t. ! lamemp3enc ! id3v2mux ! filesink location=test.mp3


class Example(QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.station=radio_db[0][0]
        self.old_title=""

        # Source for icons
        # https://icons8.com/icon/set/media-player/all
        self.app_icon=QIcon(icons_dir+"/audio-wave-64.png")
        self.play_icon=QIcon(icons_dir+"/play-64.png")
        self.stop_icon=QIcon(icons_dir+"/stop-64.png")
        self.rec_icon=QIcon(icons_dir+"/downloads-64.png")
        self.mute_icon=QIcon(icons_dir+"/mute-64.png")

        # control volume, should be between 1.0 to 10.0
        self.volMultiple=5.0 

        # Maintain state on whether we are playing or not
        self.playing=0
        
        # Maintain state on recording is on or not
        self.recording=0
        
        self.initUI()
        self.initPlayer()
        
    ####################
    # GUI handling
    ####################
    def initUI(self):
        # reference on PyQt5 tutorial
        # http://zetcode.com/gui/pyqt5/
        # reference on AT classes
        # https://doc.qt.io/qt-5/classes.html

        label = QLabel("Radio station: ", self)

        combo = QComboBox(self)
        for i in radio_db:
            combo.addItem(i[0])
        combo.activated[int].connect(self.onActivated)

        self.playBtn=QPushButton(self)
        self.playBtn.setDefault(1)
        self.playBtn.setCheckable(1)
        self.playBtn.setIcon(self.play_icon)
        self.playBtn.resize(self.playBtn.sizeHint())
        self.playBtn.clicked.connect(self.onPlay)

        self.stopBtn=QPushButton(self)
        self.stopBtn.setCheckable(1)
        self.stopBtn.setIcon(self.stop_icon)
        self.stopBtn.resize(self.stopBtn.sizeHint())
        self.stopBtn.clicked.connect(self.onStop)

        self.recBtn=QPushButton(self)
        self.recBtn.setCheckable(1)
        self.recBtn.setIcon(self.rec_icon)
        self.recBtn.resize(self.recBtn.sizeHint())
        self.recBtn.clicked.connect(self.onRec)

        self.log=QPlainTextEdit()
        self.log.setReadOnly(1)
        self.log.setWordWrapMode(0) # No text wrap
        
        self.muteBtn=QPushButton(self)
        self.muteBtn.setCheckable(1)
        self.muteBtn.setIcon(self.mute_icon)
        self.muteBtn.resize(QSize(8,8))
        self.muteBtn.clicked.connect(self.onMute)

        self.volCtrl=QSlider(self)
        self.volCtrl.setRange(0,100)
        self.volCtrl.setValue(int(100/self.volMultiple))
        self.volCtrl.valueChanged.connect(self.onVolChanged)

        hbox1=QHBoxLayout()
        #hbox.addStretch(1)
        hbox1.addWidget(label)
        hbox1.addWidget(combo)
        hbox1.addWidget(self.playBtn)
        hbox1.addWidget(self.stopBtn)
        hbox1.addWidget(self.recBtn)

        vbox1=QVBoxLayout()
        #vbox.addStretch(1)
        vbox1.addLayout(hbox1)
        vbox1.addWidget(self.log)

        hbox2=QHBoxLayout()
        hbox2.addSpacing(8)
        hbox2.addWidget(self.volCtrl)
        hbox2.addSpacing(8)

        vbox2=QVBoxLayout()
        vbox2.addWidget(self.muteBtn)
        vbox2.addLayout(hbox2)
        
        hbox=QHBoxLayout()
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)
        
        self.setLayout(hbox)
         
        self.setGeometry(300, 300, 400, 200)
        self.setWindowIcon(self.app_icon)
        self.setWindowTitle('Online Radio Client')
        self.show()

    def closeEvent(self, event):
        self.pipeline.set_state(Gst.State.NULL)
        self.mainloop.quit()
        event.accept()
        
    def onActivated(self, idx):
        # when changing station, do the following
        # 1. stop playing old station
        # 2. switch to new station
        # 3. play new station

        # 1. If playing, stop playing
        self.stop()
            
        # 2. Swtich to new station
        #self.pipeline.set_state(Gst.State.NULL)
        self.station=radio_db[idx][0]
        self.setWindowTitle(radio_db[idx][0])
        self.http_source.set_property("location", radio_db[idx][1])
        self.log.appendPlainText("%s: Switch to station %s"
                                 % (time.asctime(time.localtime()),
                                    self.station))

        # 3. Start playing new station
        self.play()
        
    def onPlay(self):
        self.play()

    def onStop(self):
        self.stop()

    def onRec(self):
        if self.recording:
            self.log.appendPlainText("%s: Recording stop"
                                 % (time.asctime(time.localtime())))
            self.filesink.set_state(Gst.State.NULL)
            self.filesink.set_property("location", "/dev/null")
            self.filesink.set_state(Gst.State.PLAYING)
            self.recording=0
        else:
            if self.playing:
                now=time.strftime("%y%m%d_%H%M%S")
                self.log.appendPlainText("%s: Recording started"
                                         % time.asctime(time.localtime()))
                self.filesink.set_state(Gst.State.NULL)
                self.filesink.set_property("location", "%s_%s.mp3" %
                                           (now, self.station))
                self.filesink.set_state(Gst.State.PLAYING)
                self.recording=1
            else:
                self.log.appendPlainText("Recording not started. " +
                                         "No playing stream")
                self.recBtn.setChecked(0)
    
    def onMute(self):
        if self.muteBtn.isChecked():
            self.play_audio.set_property("mute", 1)
        else :
            self.play_audio.set_property("mute", 0)
            
    def onVolChanged(self, event):
        pos=self.volCtrl.sliderPosition()
        self.play_audio.set_property("volume", self.volMultiple*pos/100.0)
        #print(self.play_audio.get_property("volume"))
        if pos==0:
            self.muteBtn.setChecked(1)
            self.play_audio.set_property("mute", 1)
        else:
            self.muteBtn.setChecked(0)
            self.play_audio.set_property("mute", 0)
        #if self.volCtrl.event(QEvent.MouseButtonPress):
        QToolTip.showText(QCursor.pos(), "%d" % pos, self)

    def play(self):
        self.playing=1
        self.playBtn.setChecked(1)
        self.stopBtn.setChecked(0)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop.run()

    def stop(self):
        self.playing=0
        self.playBtn.setChecked(0)
        self.stopBtn.setChecked(1)
        self.pipeline.set_state(Gst.State.NULL)
        self.mainloop.quit()

        
    ####################
    # GStreamer
    ####################
    def initPlayer(self):
        # General reference on GStreamer
        # https://gstreamer.freedesktop.org/documentation/tutorials/index.html
        # General reference on using pygst
        # http://brettviren.github.io/pygst-tutorial-org/pygst-tutorial.html
        Gst.init(None)
        self.mainloop=GObject.MainLoop()
        self.pipeline=Gst.Pipeline.new("pipeline")

        # souphttpsource -> decodebin -> audioconvert -> tee -> playsink
        #                                                    -> lamemp3enc -> id3v2mux -> filesink

        self.http_source=Gst.ElementFactory.make("souphttpsrc", "http_source")
        self.http_source.set_property("location", radio_db[0][1])
        self.http_source.set_property("iradio-mode", "true")
        self.pipeline.add(self.http_source)

        decode_audio=Gst.ElementFactory.make("decodebin", "decode_audio")
        self.pipeline.add(decode_audio)
        ret=self.http_source.link(decode_audio)

        self.audio_convert=Gst.ElementFactory.make("audioconvert", "audio_convert")
        self.pipeline.add(self.audio_convert)
        ret=ret and decode_audio.connect("pad-added",self.decodeAudioPad)

        tee=Gst.ElementFactory.make("tee", "tee")
        self.pipeline.add(tee)
        ret=ret and self.audio_convert.link(tee)
        
        self.play_audio=Gst.ElementFactory.make("playsink", "play_audio")
        self.pipeline.add(self.play_audio)
        ret=ret and tee.link(self.play_audio)
        self.play_audio.set_property("volume", 1.0)

        lamemp3enc=Gst.ElementFactory.make("lamemp3enc", "lamemp3enc")
        self.pipeline.add(lamemp3enc)
        ret=ret and tee.link(lamemp3enc)

        id3v2mux=Gst.ElementFactory.make("id3v2mux", "id3v2mux")
        self.pipeline.add(id3v2mux)
        ret=ret and lamemp3enc.link(id3v2mux)
        
        self.filesink=Gst.ElementFactory.make("filesink", "filesink")
        self.pipeline.add(self.filesink)
        ret=ret and id3v2mux.link(self.filesink)
        self.filesink.set_property("location", "/dev/null")

        if not ret:
            print("ERROR: Elements could not be linked")
            sys.exit(1)

        self.bus=self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.onMessage)

    def decodeAudioPad(self, element, pad):
        pad.link(self.audio_convert.get_static_pad("sink"))
        
    def onMessage(self, bus, message):
        # refernce on parsing tag
        # https://gist.github.com/fossfreedom/37ee44971e9f4950e561
        #print(message.type)
        if message.type==Gst.MessageType.TAG:
            taglist=message.parse_tag()
            for i in range(taglist.n_tags()):
                name = taglist.nth_tag_name(i)
                if name == "title":
                    new_title=taglist.get_string(name)[1]
                    if new_title != self.old_title:
                        self.old_title=new_title
                        self.log.appendPlainText('%s: %s' %
                                (time.asctime(time.localtime()), new_title))
                        self.setWindowTitle("%s: %s" %(self.station, new_title))

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
