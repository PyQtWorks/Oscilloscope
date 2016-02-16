# -*- coding: utf-8 -*-

from PyQt5.QtGui import QColor

import wave, struct
from signal import signal

class Channel():

    def __init__(self, name, tila):
        self.name = name
        self.file = None
        self.signal = None
        self.length = 0
        self.index = 0
        self.state = tila   # kanava päällä
        self.ypos = 0
        self.voltage = 1
        self.scale = 1
        self.drawColor = QColor(255, 0, 0)
        
    def ReadFile(self, file):
        
        """ Lukee annetun tiedoston ja tallentaa signaalin desimaalilukuina listaan.
            Poikkeustilanteet käsitellään Oskilloskoopin puolella. """
        
        # ei tiedostoa
        if file == "":
            return False
        
        # WAV
        if file.split(".")[-1] == "wav":
            try:
                data = wave.open(file, 'r')
                
                params = data.getparams() # nchannels, samplewidth (bytes), samplerate, nframes, compression, compname
                
                #print("Wav file \"{}\"".format(file.split("/")[-1]))
                #print("Channels: {}, Samplewidth: {}, Samplerate: {}, Frames: {}, Length: {} s\n".format(params[0], params[1], params[2], params[3], float(params[3])/float(params[2])))
                
                if not params[1] == 2:                              # 16 bit
                    raise SyntaxError
                
                if not params[0] == 1:                              # mono
                    raise NameError
               
                if float(params[3])/float(params[2]) < 1.0:         # alle 1 sec
                    raise RuntimeError

                frames = data.readframes(data.getnframes())         # data bitteinä (string of bytes)

                signaali = struct.unpack("%ih" % params[3], frames) # muunnetaan signed short intiksi (16 bit) 
                
                signaali = [float(x)/(2**15) for x in signaali]     # muunnetaan desimaaliluvuksi -1.0...1.0
                                                                    # 16 bit int = arvot -32768...32767 (2^15)
                self.signal = signaali
                self.length = len(signaali)
                self.file = file
                return True
                
            
            finally:
                if data:
                    data.close()
        
        # CSV
        elif file.split(".")[-1] == "csv":
        
            try:
                data = open(file, 'r')
            
                signaali = [float(x.strip()) for x in data]         # tallennetaan desimaaliluvuksi
                
                if len(signaali) < 48000: # < 1 sec
                    raise RuntimeError
            
                self.signal = signaali
                self.length = len(signaali)
                self.file = file
                return True
                
            finally:
                if data:
                    data.close()
                   
        # Tiedosto jotain muuta tyyppiä            
        else:
            raise TypeError
                
    def PrintInfo(self):
        print("CHANNEL", self.name)
        print("state: ", self.state)  
        print("file: ", self.file)
        print("length: ", self.length)
        print("ypos: ", self.ypos)
        print("voltage: ", self.voltage) 
        print("scale: ", self.scale)
        print("color: ", self.drawColor.getRgb(), "\n")