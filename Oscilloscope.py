# -*- coding: utf-8 -*-

import sys, math
from PyQt5 import QtCore
from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtCore import Qt, QT_VERSION_STR, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QIcon, QPixmap, QBrush, QPalette, QFont
from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QDockWidget, QApplication, QMessageBox, QColorDialog, QCheckBox, QDial, QMenu, QActionGroup,
                             QAction, QTextEdit, QFileDialog, QSlider, QLCDNumber, QLabel, QPushButton, QGridLayout, QDialog, QMenuBar, QStatusBar, QWidget, QComboBox, QRadioButton) 
     
from channel import Channel
from timeit import default_timer as timer

# PIIRTOIKKUNA
class Display(QLabel):
    
    backgroundcolor = QColor(255, 255, 255)
    index = 0   # XYSäi
    grid = 48   # yksi ruutu 48 pikselia -> helppo sovitus kun Fs = 48 kHz tai sen moninkerta
    speed = 1
    
    def __init__(self, parent):
        super().__init__(parent)
        self.initDisplay()
        self.time = 0
        
    def initDisplay(self):
        
        self.setMinimumSize(22*48, 8*48) # asetetaan ruudun minimikooksi 24 vaakaruutua ja 8 pystyruutua
        self.setFrameStyle(6)
        self.setLineWidth(1)
        self.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.setAutoFillBackground(True)
        self.setStyleSheet("QLabel {border-style: solid; border-width: 2px; border-radius: 0px; "\
            "border-color: black;" + "background-color: rgb({:}, {:}, {:})"\
            .format(self.backgroundcolor.red(), self.backgroundcolor.green(), self.backgroundcolor.blue()) +"}")
     
    def showBackgroundColorDialog(self): 
        # Taustavärin valinta
        self.backgroundcolor = QColorDialog.getColor()
        self.setStyleSheet("QLabel {border-style: solid; border-width: 2px; border-radius: 0px; "\
            "border-color: black;" + "background-color: rgb({:}, {:}, {:})"\
            .format(self.backgroundcolor.red(), self.backgroundcolor.green(), self.backgroundcolor.blue()) +"}") 
        
    def resetStyleSheet(self):
        # QMESSAGEBOX STYLESHEET KORVAA MYÖS TAUSTAN TYYLIN JOSTAIN SYYSTÄ -> TÄYTYY ASETTAA UUSIKSI           
        self.setStyleSheet("QLabel {border-style: solid; border-width: 2px; border-radius: 0px; "\
        "border-color: black;" + "background-color: rgb({:}, {:}, {:})"\
        .format(self.backgroundcolor.red(), self.backgroundcolor.green(), self.backgroundcolor.blue()) +"}")  
        
    def ErrorPopup(self, text):
        # Luo messagebox -ikkunan annetulla tekstillä 
        self.setStyleSheet(".QMessageBox {border-width: 0px; font: bold 12px; }")  
        QMessageBox.warning(self, "Error!\n", text)                 
        
    def paintEvent(self, e):
        
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        self.drawGrid(qp)
        if Oscilloscope.settings.on == True:

            if Oscilloscope.settings.mode == "XY":
                self.XYmode(qp)
            else:
                self.NormalMode(qp)

        self.resetStyleSheet()
        qp.end() 
    
    # taustaruudukko
    def drawGrid(self, qp):                                     

        # keskiviivat
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        qp.setPen(pen)
        qp.drawLine(0, self.height()/2, self.width(), self.height()/2)
        qp.drawLine(self.width()/2, 0, self.width()/2, self.height())
        
        # muut viivat
        pen = QPen(Qt.darkGray, 1, Qt.SolidLine)
        qp.setPen(pen)
        
        i = self.height()/2 + self.grid     
        while i < self.height():
            qp.drawLine(0, i, self.width(), i)
            i += self.grid
            
        i = self.height()/2 - self.grid     
        while i > 0:
            qp.drawLine(0, i, self.width(), i)
            i -= self.grid
            
        i = self.width()/2 + self.grid     
        while i < self.width():
            qp.drawLine(i, 0, i, self.height())
            i += self.grid
            
        i = self.width()/2 - self.grid     
        while i > 0:
            qp.drawLine(i, 0, i, self.height())
            i -= self.grid  

    def NormalMode(self, qp):

        if Oscilloscope.Kanava1.state == True and Oscilloscope.Kanava1.signal == None:
            Oscilloscope.settings.on = False
            self.ErrorPopup("Channel 1 signal file missing!")
                           
        elif Oscilloscope.Kanava2.state == True and Oscilloscope.Kanava2.signal == None:
            Oscilloscope.settings.on = False
            self.ErrorPopup("Channel 2 signal file missing!")
            
        elif Oscilloscope.Kanava2.state == True and Oscilloscope.Kanava1.signal == None:
            Oscilloscope.settings.on = False
            self.ErrorPopup("Channel 1 signal file missing!\n\n\
Can't use internal triggering. Give channel 1 signal or use external triggering.")    
        
        elif Oscilloscope.Kanava1.state == False and Oscilloscope.Kanava2.state == False:
            pass # skipataan piirto  
            
        else:

            # yhden ruudun pituus (ms) = montako samplea per pikseli, min = 1, max = 1000
            gridlength = Oscilloscope.settings.time * Oscilloscope.settings.TimeScale 
            
            # piirretään L pikseliä, jokainen pikseli yksi tai useampi sample. 
            # Jos useampi sample per pikseli niin jätetään gridlength-1 samplea aina välistä pois.
            
            # yhden ikkunallisen pituus (ms)
            displaylength = gridlength * self.width()/48 
            
            # ikkunalliseen tarvittava määrä samplejä
            samples = gridlength * self.width() 

            # EXTERNAL TRIGGER 
            if Oscilloscope.trigger.state:
                
                if (timer()-self.time) > 0.010:                     # päivitys n. 10 ms välein -> max. päivitystaajuus 100 Hz
                    self.time = timer() 
                    Oscilloscope.trigger.index += 480                               # 10 ms sampleja
                    if Oscilloscope.trigger.index >= Oscilloscope.trigger.length:   # tiedoston pituus ylittyi
                        Oscilloscope.trigger.index = 0
                    for i in range(Oscilloscope.trigger.index, Oscilloscope.trigger.index + 480):   # etsitään triggerpistettä 10 ms pätkästä signaalia
                        if Oscilloscope.trigger.signal[i] > 0 and Oscilloscope.trigger.signal[i-1] < 0:
                            Oscilloscope.Kanava1.index = i
                            Oscilloscope.Kanava2.index = i
                            break

                # tiedosto loppuu -> aloitetaan alusta
                if Oscilloscope.Kanava1.length <= Oscilloscope.Kanava1.index + samples:
                    Oscilloscope.Kanava1.index = 0
                        
                if Oscilloscope.Kanava2.length <= Oscilloscope.Kanava2.index + samples:
                    Oscilloscope.Kanava2.index = 0
                
            # NORMAALI TRIGGER
            else:

                TriggerLevel = Oscilloscope.trigger.voltage * Oscilloscope.trigger.scale
                
                # verrataan kulunutta aikaa ikkunan kestoon, jotta tiedetään milloin voidaan piirtää seuraava pala signaalia. 
                # Muuten piirretään uudelleen vanhaa signaalia.
                if (timer()-self.time) > displaylength/(self.speed*1000):        
                    Oscilloscope.Kanava1.index += samples           # kasvatetaan indeksiä seuraavan ikkunallisen verran
                    Oscilloscope.Kanava2.index += samples
                    self.time = timer()
                    
                # tiedosto loppuu -> aloitetaan alusta
                if Oscilloscope.Kanava1.length <= Oscilloscope.Kanava1.index + samples:
                    Oscilloscope.Kanava1.index = 0
                        
                if Oscilloscope.Kanava2.length <= Oscilloscope.Kanava2.index + samples:
                    Oscilloscope.Kanava2.index = 0    
                
                trigger = True          # looppausehto
                
                if Oscilloscope.Kanava1.index == 0:         # ollaan tiedoston alussa
                    zerocross = True
                else:
                    zerocross = False

                # löytyykö triggerpistettä ollenkaan signaalin pätkästä
                if max(Oscilloscope.Kanava1.signal[Oscilloscope.Kanava1.index:(Oscilloscope.Kanava1.index + samples)]) - TriggerLevel >= 0 and \
                   min(Oscilloscope.Kanava1.signal[Oscilloscope.Kanava1.index:(Oscilloscope.Kanava1.index + samples)]) - TriggerLevel <= 0: 
                    
                    # Haetaan trigger indeksi
                    while trigger:
                        
                        # signaali käynyt negatiivisena tai minimissä
                        if Oscilloscope.Kanava1.signal[Oscilloscope.Kanava1.index] < 0 or \
                        abs(Oscilloscope.Kanava1.signal[Oscilloscope.Kanava1.index] - min(Oscilloscope.Kanava1.signal[Oscilloscope.Kanava1.index:(Oscilloscope.Kanava1.index + samples)])) < 0.1:
                            zerocross = True
                    
                        if (Oscilloscope.Kanava1.signal[Oscilloscope.Kanava1.index] - TriggerLevel >= 0) and (Oscilloscope.Kanava1.signal[Oscilloscope.Kanava1.index-1] < Oscilloscope.Kanava1.signal[Oscilloscope.Kanava1.index]) and zerocross:
                            trigger = False # lopetetaan loop, muuten kasvatetaan indeksiä
                        else:    
                            Oscilloscope.Kanava1.index += 1
                            Oscilloscope.Kanava2.index += 1
                        
                        # tiedoston koko ylittyi, jatketaan triggerpisteen hakemista tiedoston alusta
                        if Oscilloscope.Kanava1.length <= Oscilloscope.Kanava1.index + samples:
                            Oscilloscope.Kanava1.index = 0
                        
                        if Oscilloscope.Kanava2.length <= Oscilloscope.Kanava2.index + samples:
                            Oscilloscope.Kanava2.index = 0          
            
            # PIIRRETÄÄN SIGNAALIT

            # CHANNEL 1
            if Oscilloscope.Kanava1.state == True:
                self.drawSignal(qp, Oscilloscope.Kanava1, gridlength)

            # CHANNEL 2
            if Oscilloscope.Kanava2.state == True:
                self.drawSignal(qp, Oscilloscope.Kanava2, gridlength)
                
            # skaalaus:
            gridVoltage1 = Oscilloscope.Kanava1.voltage * Oscilloscope.Kanava1.scale    # yksi ruutu 0,001...10 V
            gridVoltage2 = Oscilloscope.Kanava2.voltage * Oscilloscope.Kanava2.scale  
            
            # INFOT    
            text = "TIME: {:.1f} ms ; {:.1f} ms".format(gridlength, displaylength)    
                
            if gridVoltage1 < 0.1:    
                text1 = "CH1:  {:.1f} mV ; {:.1f} mV".format(gridVoltage1*1000, gridVoltage1*self.height()*1000/48)
            else:
                text1 = "CH1:  {:.1f} V ; {:.1f} V".format(gridVoltage1, gridVoltage1*self.height()/48) 
             
            if gridVoltage2 < 0.1:    
                text2 = "CH2:  {:.1f} mV ; {:.1f} mV".format(gridVoltage2*1000, gridVoltage2*self.height()*1000/48)
            else:
                text2 = "CH2:  {:.1f} V ; {:.1f} V".format(gridVoltage2, gridVoltage2*self.height()/48)
                
            qp.setPen(QColor(240, 0, 0))
            qp.setFont(QFont('Decorative', 8))
            qp.drawText(8,16, text)
            qp.drawText(8,30, text1)
            qp.drawText(8,45, text2)  
            
    def drawSignal(self, qp, kanava, gridlength):
        
        """ Piirtää annetun kanavan signaalia yhden ikkunallisen verran """
        
        # skaalaus:
        gridVoltage = kanava.voltage * kanava.scale    # yksi ruutu 0,001...10 V
                
        if kanava.signal == None:               # onko signaalia
            Oscilloscope.settings.on = False
            self.ErrorPopup("Channel " + kanava.name + " signal file missing!")
            
        else:
            pen = QPen(kanava.drawColor, 2, Qt.SolidLine)
            qp.setPen(pen)
            
            xprev = 2                           # border = 2 px
            yprev = self.height()/2 - (kanava.signal[kanava.index]*48)/gridVoltage - kanava.ypos
            
            for i in range(0, self.width()-2):
                x = i + 2
                y = self.height()/2 - (kanava.signal[kanava.index + i*gridlength]*48)/gridVoltage - kanava.ypos
                qp.drawLine(xprev + Oscilloscope.settings.xpos, yprev, x + Oscilloscope.settings.xpos, y)
                xprev = x
                yprev = y 
              
    def XYmode(self, qp):
        
        # Ch1 vaaka-akseli, Ch2 pysty

        if Oscilloscope.Kanava1.signal == None:
            Oscilloscope.settings.on = False
            self.ErrorPopup("Channel 1 signal file missing!")
            
        elif Oscilloscope.Kanava2.signal == None:
            Oscilloscope.settings.on = False
            self.ErrorPopup("Channel 2 signal file missing!")
            
        elif Oscilloscope.Kanava1.length != Oscilloscope.Kanava2.length:
            Oscilloscope.settings.on = False
            self.ErrorPopup("Signals files are not the same length")    
        
        else:

            # yhden ruudun samplet per näytteenottotaajuus (näytettä sekunnissa) = ruudun kesto sekunneissa
            if (timer()-self.time) > self.width()/48000: 
                self.index += self.width()                  # kasvatetaan indeksiä ikkunan pituuden verran
                self.time = timer()                         # päivitetään aika
                
            # tiedosto loppuu kesken -> loopataan alkuun
            if Oscilloscope.Kanava1.length <= self.index + self.width():
                self.index = 0    
            
            # piirto
            pen = QPen(Oscilloscope.Kanava1.drawColor, 2, Qt.SolidLine)
            qp.setPen(pen)
            
            # skaalaus:
            gridVoltage1 = Oscilloscope.Kanava1.voltage * Oscilloscope.Kanava1.scale    # yksi ruutu 0,001...10 V
            gridVoltage2 = Oscilloscope.Kanava2.voltage * Oscilloscope.Kanava2.scale

            xprev = self.width()/2 + (Oscilloscope.Kanava1.signal[self.index]*48)/gridVoltage1 + Oscilloscope.Kanava1.ypos
            yprev = self.height()/2 - (Oscilloscope.Kanava2.signal[self.index]*48)/gridVoltage2 - Oscilloscope.Kanava2.ypos
                
            for i in range(0, self.width()):
                x = self.width()/2 + (Oscilloscope.Kanava1.signal[self.index + i]*48/gridVoltage1) + Oscilloscope.Kanava1.ypos
                y = self.height()/2 - (Oscilloscope.Kanava2.signal[self.index + i]*48)/gridVoltage2 - Oscilloscope.Kanava2.ypos
                qp.drawLine(xprev, yprev, x, y)     # piirretään viiva pisteestä (xprev, yprev) pisteeseen (x, y)
                xprev = x
                yprev = y 
                
            if gridVoltage1 < 0.1:    
                text1 = "CH1:  {:.1f} mV ; {:.1f} mV".format(gridVoltage1*1000, gridVoltage1*self.height()*1000/48)
            else:
                text1 = "CH1:  {:.1f} V ; {:.1f} V".format(gridVoltage1, gridVoltage1*self.height()/48) 
             
            if gridVoltage2 < 0.1:    
                text2 = "CH2:  {:.1f} mV ; {:.1f} mV".format(gridVoltage2*1000, gridVoltage2*self.width()*1000/48)
            else:
                text2 = "CH2:  {:.1f} V ; {:.1f} V".format(gridVoltage2, gridVoltage2*self.width()/48)
                
            qp.setPen(QColor(240, 0, 0))
            qp.setFont(QFont('Decorative', 8))
            qp.drawText(8,30, text1)
            qp.drawText(8,45, text2)                      

# YLEISASETUKSET
class Settings():

    def __init__(self):
        self.xpos = 0
        self.time = 1
        self.TimeScale = 1
        self.mode = "normal"
        self.on = False
        
    def PrintInfo(self):
        print("*** SETTINGS")
        print("xpos: ", self.xpos)
        print("time: ", self.time) 
        print("scale: ", self.TimeScale)   

# PÄÄIKKUNA                
class Oscilloscope(QMainWindow):
    
    Kanava1 = Channel("1", True)            # Alustetaan kanavat, bool = kanava päällä vai ei oletuksena
    Kanava2 = Channel("2", False)
    trigger = Channel("Trigger", False)     # False = normaali trigger, True = external
    settings = Settings()
    
    Kanava2.drawColor = QColor(0,0,255)     # vaihdetaan vakio piirtoväri
    trigger.scale = 0.001
    VoltageLink = False                     # voltagelink -asetuksen oletustila
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self): 
        
        self.setGeometry(0, 0, 1258, 720)   # ikkunan koko
        self.center()                       # keskitä näytölle
        self.setWindowIcon(QIcon('Media/icon.png'))  
        self.setWindowTitle('Oscilloscope') 
        
        self.ikkuna = Display(self)         # piirtoikkuna
    
        self.statusBar = QStatusBar()       # statusbar
        self.setStatusBar(self.statusBar)

        self.dock = QDialog()               # Pääikkunan keskelle Wigdet, johon kaikki tavara tulee
        self.setCentralWidget(self.dock)
        
        # sliderien skaalauksen valinta    
        self.skaala1 = QComboBox()          # ch1 volt
        self.skaala2 = QComboBox()          # ch2 volt
        self.skaala3 = QComboBox()          # aika  
        self.TriggerSkaala = QComboBox()    # trigger
        aikaskaala = ["ms", "10ms"]
        volttiskaala = ["mV", "10mV", "100mV", "V"] 
        
        self.skaala1.addItems(volttiskaala)
        self.skaala2.addItems(volttiskaala)
        self.skaala3.addItems(aikaskaala)
        self.TriggerSkaala.addItems(volttiskaala)   
        
        self.skaala1.setCurrentIndex(3)
        self.skaala2.setCurrentIndex(3) 
        self.skaala3.setCurrentIndex(0)
        self.TriggerSkaala.setCurrentIndex(0)      
        
        self.skaala1.setStatusTip('Choose voltage scale')
        self.skaala2.setStatusTip('Choose voltage scale')
        self.skaala3.setStatusTip('Choose time scale')
        self.TriggerSkaala.setStatusTip('Choose voltage scale')
        
        # lukuarvonäytöt
        lcd1 = QLCDNumber(self)
        lcd1.setSegmentStyle(2)
        lcd1.setFixedSize(70,30)
        
        lcd2 = QLCDNumber(self)
        lcd2.setSegmentStyle(2)
        lcd2.setFixedSize(70,30)
        
        lcd3 = QLCDNumber(self)
        lcd3.setSegmentStyle(2)
        lcd3.setFixedSize(70,30)
        
        lcd4 = QLCDNumber(self)
        lcd4.setSegmentStyle(2)
        lcd4.setFixedSize(70,30)
        
        lcd5 = QLCDNumber(self)
        lcd5.setSegmentStyle(2)
        lcd5.setFixedSize(70,30)
        
        lcd6 = QLCDNumber(self)
        lcd6.setSegmentStyle(2)
        lcd6.setFixedSize(70,30)
        
        # sliderit
        minSliderWidth = 70 # Sliderien minimipituus
        
        self.sld1 = QSlider(Qt.Horizontal, self)
        self.sld1.setMinimumWidth(minSliderWidth)
        
        self.sld2 = QSlider(Qt.Horizontal, self)
        self.sld2.setMinimumWidth(minSliderWidth)
        
        self.sld3 = QSlider(Qt.Horizontal, self)
        self.sld3.setMinimumWidth(minSliderWidth)
        
        self.sld4 = QSlider(Qt.Horizontal, self)
        self.sld4.setMinimumWidth(minSliderWidth)
        
        self.sld5 = QSlider(Qt.Horizontal, self)
        self.sld5.setMinimumWidth(minSliderWidth)
        
        self.sld6 = QSlider(Qt.Horizontal, self)
        self.sld6.setMinimumWidth(minSliderWidth)
        
        self.sld1.setRange(-100,100)    # ch1 ypos
        self.sld1.setValue(0)
        
        self.sld2.setRange(1,10)        # ch1 volt
        self.sld2.setValue(1)
        self.sld2.setTickInterval(1)
        self.sld2.setTickPosition(2)
        self.sld2.setPageStep(1)
        
        self.sld3.setRange(-100,100)    # ch2 ypos
        self.sld3.setValue(0)
        
        self.sld4.setRange(1,10)        # ch2 volt
        self.sld4.setValue(1)
        self.sld4.setTickInterval(1)
        self.sld4.setTickPosition(2)
        self.sld4.setPageStep(1)
        
        self.sld5.setRange(-125,125)    # xpox
        self.sld5.setValue(0)
        
        self.sld6.setRange(1,10)        # aika
        self.sld6.setValue(1)
        self.sld6.setTickInterval(1)
        self.sld6.setTickPosition(2)
        self.sld6.setPageStep(1)
        
        self.sld1.setStatusTip('Move slider to change the value')
        self.sld2.setStatusTip('Move slider to change the value')
        self.sld3.setStatusTip('Move slider to change the value')
        self.sld4.setStatusTip('Move slider to change the value')
        self.sld5.setStatusTip('Move slider to change the value')
        self.sld6.setStatusTip('Move slider to change the value')
        
        # Labelit
        lbl1 = QLabel(self)
        lbl1.setText("Ypos")
        
        lbl2 = QLabel(self)
        lbl2.setText("Volts")
        
        lbl3 = QLabel(self)
        lbl3.setText("Ypos")
        
        lbl4 = QLabel(self)
        lbl4.setText("Volts")
        
        lbl5 = QLabel(self)
        lbl5.setText("Xpos")
        
        lbl6 = QLabel(self)
        lbl6.setText("Time")
        
        lbl1.setStyleSheet("QLabel {color : red;  font: bold 14px; border-width: 0px; }")
        lbl2.setStyleSheet("QLabel {color : black; font: bold 14px; border-width: 0px; }")
        lbl3.setStyleSheet("QLabel {color : red;  font: bold 14px; border-width: 0px; }")
        lbl4.setStyleSheet("QLabel {color : black; font: bold 14px; border-width: 0px; }")
        lbl5.setStyleSheet("QLabel {color : red;  font: bold 14px; border-width: 0px; }")
        lbl6.setStyleSheet("QLabel {color : black; font: bold 14px; border-width: 0px; }")
        
        lbl1.setStatusTip('Adjust vertical position')
        lbl3.setStatusTip('Adjust vertical position')
        lbl5.setStatusTip('Adjust horizontal position')
        lbl2.setStatusTip('Voltage per division')
        lbl4.setStatusTip('Voltage per division')
        lbl6.setStatusTip('Time per division')
        
        # Reset napit
        ResetY1 = QPushButton('Reset', self)
        ResetY1.setFixedSize(40,30)
        ResetY1.clicked.connect(self.button1Event) 
        
        ResetV1 = QPushButton('Reset', self)
        ResetV1.setFixedSize(40,30)
        ResetV1.clicked.connect(self.button2Event)   

        ResetY2 = QPushButton('Reset', self)
        ResetY2.setFixedSize(40,30)
        ResetY2.clicked.connect(self.button3Event)
        
        ResetV2 = QPushButton('Reset', self)
        ResetV2.setFixedSize(40,30)
        ResetV2.clicked.connect(self.button4Event) 
        
        ResetH = QPushButton('Reset', self)
        ResetH.setFixedSize(40,30)
        ResetH.clicked.connect(self.button5Event)   

        ResetT = QPushButton('Reset', self)
        ResetT.setFixedSize(40,30)
        ResetT.clicked.connect(self.button6Event)
        
        ResetY1.setStyleSheet("QPushButton { background-color: red; border-style: outset; "\
                                "border-width: 2px; border-radius: 8px; border-color: grey; font: bold 10px;}" \
                                "QPushButton:pressed {background-color: rgb(160, 0, 0); border-style: inset;}")
        
        ResetV1.setStyleSheet("QPushButton { background-color: red; border-style: outset; "\
                                "border-width: 2px; border-radius: 8px; border-color: grey; font: bold 10px;}" \
                                "QPushButton:pressed {background-color: rgb(160, 0, 0); border-style: inset;}")
        
        ResetY2.setStyleSheet("QPushButton { background-color: red; border-style: outset; "\
                                "border-width: 2px; border-radius: 8px; border-color: grey; font: bold 10px;}" \
                                "QPushButton:pressed {background-color: rgb(160, 0, 0); border-style: inset;}")
        
        ResetV2.setStyleSheet("QPushButton { background-color: red; border-style: outset; "\
                                "border-width: 2px; border-radius: 8px; border-color: grey; font: bold 10px;}" \
                                "QPushButton:pressed {background-color: rgb(160, 0, 0); border-style: inset;}")
        
        ResetH.setStyleSheet("QPushButton { background-color: red; border-style: outset; "\
                                "border-width: 2px; border-radius: 8px; border-color: grey; font: bold 10px;}" \
                                "QPushButton:pressed {background-color: rgb(160, 0, 0); border-style: inset;}")
        
        ResetT.setStyleSheet("QPushButton { background-color: red; border-style: outset; "\
                                "border-width: 2px; border-radius: 8px; border-color: grey; font: bold 10px;}" \
                                "QPushButton:pressed {background-color: rgb(160, 0, 0); border-style: inset;}")
         
        ResetY1.setStatusTip('Reset to default value')
        ResetV1.setStatusTip('Reset to default value')
        ResetY2.setStatusTip('Reset to default value')
        ResetV2.setStatusTip('Reset to default value')
        ResetH.setStatusTip('Reset to default value')
        ResetT.setStatusTip('Reset to default value')
         
        # Yhdistetään elementit
        lcd1.display(self.sld1.value())
        self.sld1.valueChanged.connect(lcd1.display)
        self.sld1.valueChanged[int].connect(self.changeValue1)
        
        lcd2.display(self.sld2.value())
        self.sld2.valueChanged.connect(lcd2.display)
        self.sld2.valueChanged[int].connect(self.changeValue2)
        
        lcd3.display(self.sld3.value())
        self.sld3.valueChanged.connect(lcd3.display)
        self.sld3.valueChanged[int].connect(self.changeValue3)
        
        lcd4.display(self.sld4.value())
        self.sld4.valueChanged.connect(lcd4.display)
        self.sld4.valueChanged[int].connect(self.changeValue4)
        
        lcd5.display(self.sld5.value())
        self.sld5.valueChanged.connect(lcd5.display)
        self.sld5.valueChanged[int].connect(self.changeValue5)
        
        lcd6.display(self.sld6.value())
        self.sld6.valueChanged.connect(lcd6.display)
        self.sld6.valueChanged[int].connect(self.changeValue6)
        
        self.skaala1.currentIndexChanged[int].connect(self.skaala1changed)
        self.skaala2.currentIndexChanged[int].connect(self.skaala2changed)
        self.skaala3.currentIndexChanged[int].connect(self.skaala3changed)
        self.TriggerSkaala.currentIndexChanged[int].connect(self.TriggerSkaalachanged)
        
        ################################################################

        """ CHANNEL 1 """
        
        # ch1 ikkuna
        channel1 = QLabel()
        channel1.setMinimumSize(346, 172)
        channel1.setMaximumHeight(172)
        channel1.setFrameStyle(6)
        channel1.setStyleSheet("QLabel {border-style: outset; border-width: 2px; border-radius: 15px; border-color: black; background-color: rgb(249, 249, 250)}")
        channel1.setLineWidth(1)
        channel1.setAutoFillBackground(True)
        
        # ch1 label
        Ch1Label = QLabel()
        Ch1Label.setText("CHANNEL 1")
        Ch1Label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        Ch1Label.setStyleSheet(".QLabel {max-height: 16px; border-width: 0px; font: bold 14px;}")
        Ch1Label.setStatusTip('Channel 1 settings')
        
        # ch1 file label
        self.Ch1filelabel = QLabel()
        self.Ch1filelabel.setText("")
        self.Ch1filelabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.Ch1filelabel.setStyleSheet(".QLabel {max-height: 16px; border-width: 0px; font: italic 14px; color: darkRed ;}")
        
        # on / off nappi
        self.OnOff1 = QCheckBox('On', self)
        self.OnOff1.toggle()
        self.OnOff1.setStyleSheet(".QCheckBox {font: bold 14px;}")
        self.OnOff1.stateChanged.connect(self.Channel1StateChange)
        self.OnOff1.setStatusTip('Turn channel 1 on or off')
        
        # ch1 grid
        gridCh1 = QGridLayout()
        gridCh1.setSpacing(10)
        channel1.setLayout(gridCh1)
        
        gridCh1.addWidget(Ch1Label, 0, 0, 1, 5)
        gridCh1.addWidget(self.OnOff1, 0, 4)
        gridCh1.addWidget(self.Ch1filelabel, 1, 0, 1, 5)
        
        gridCh1.addWidget(lbl1, 2, 0)
        gridCh1.addWidget(lbl2, 3, 0)
        
        gridCh1.addWidget(self.sld1, 2, 1)
        gridCh1.addWidget(self.sld2, 3, 1)
        
        gridCh1.addWidget(lcd1, 2, 2)
        gridCh1.addWidget(lcd2, 3, 2)
        
        gridCh1.addWidget(ResetY1, 2, 3)
        gridCh1.addWidget(ResetV1, 3, 3)
        
        gridCh1.addWidget(self.skaala1, 3, 4)
        
        ################################################################
        
        """ CHANNEL 2 """
        
        # ch2 ikkuna 
        channel2 = QLabel()
        channel2.setMinimumSize(346, 172)
        channel2.setMaximumHeight(172)
        channel2.setFrameStyle(6)
        channel2.setLineWidth(1)
        channel2.setAutoFillBackground(True)
        channel2.setStyleSheet("QLabel {border-style: outset; border-width: 2px; border-radius: 15px; border-color: black; background-color: rgb(249, 249, 250)}")
        
        # ch2 label 
        Ch2Label = QLabel()
        Ch2Label.setText("CHANNEL 2")
        Ch2Label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        Ch2Label.setStyleSheet(".QLabel {max-height: 16px; border-width: 0px; font: bold 14px;}")
        Ch2Label.setStatusTip('Channel 2 settings')
        
        # ch2 file label
        self.Ch2filelabel = QLabel()
        self.Ch2filelabel.setText("")
        self.Ch2filelabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.Ch2filelabel.setStyleSheet(".QLabel {max-height: 16px; border-width: 0px; font: italic 14px; color: darkRed }")
        
        # on / off nappi
        self.OnOff2 = QCheckBox('On', self)
        self.OnOff2.stateChanged.connect(self.Channel2StateChange)
        self.OnOff2.setStatusTip('Turn channel 2 on or off')
        self.OnOff2.setStyleSheet(".QCheckBox {font: bold 14px;}")
        
        # ch2 grid
        gridCh2 = QGridLayout()
        gridCh2.setSpacing(10)
        channel2.setLayout(gridCh2)
        
        gridCh2.addWidget(Ch2Label, 0, 0, 1, 5)
        gridCh2.addWidget(self.OnOff2, 0, 4)
        gridCh2.addWidget(self.Ch2filelabel, 1, 0, 1, 5)
        
        gridCh2.addWidget(lbl3, 2, 0)
        gridCh2.addWidget(lbl4, 3, 0)
        
        gridCh2.addWidget(self.sld3, 2, 1)
        gridCh2.addWidget(self.sld4, 3, 1)
        
        gridCh2.addWidget(lcd3, 2, 2)
        gridCh2.addWidget(lcd4, 3, 2)
        
        gridCh2.addWidget(ResetY2, 2, 3)
        gridCh2.addWidget(ResetV2, 3, 3)
        
        gridCh2.addWidget(self.skaala2, 3, 4)
        
        ################################################################
        
        """ VAAKATASO """
        
        # ikkuna
        vaakataso = QLabel()
        vaakataso.setMinimumSize(346, 172)
        vaakataso.setMaximumHeight(172)
        vaakataso.setFrameStyle(6)
        vaakataso.setLineWidth(1)
        vaakataso.setAutoFillBackground(True)
        vaakataso.setStyleSheet("QLabel {border-style: outset; border-width: 2px; border-radius: 15px; border-color: black; background-color: rgb(249, 249, 250)}")
        
        # label
        vaakaLabel = QLabel()
        vaakaLabel.setText("HORIZONTAL")
        vaakaLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        vaakaLabel.setStyleSheet(".QLabel {max-height: 16px; border-width: 0px; font: bold 14px;}")
        vaakaLabel.setStatusTip('Horizontal settings')
        
        # tyhjä file label jotta kaikki pysyy linjassa muiden elementtien kanssa
        vaakafill = QLabel()
        vaakafill.setText("")
        vaakafill.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        vaakafill.setStyleSheet(".QLabel {max-height: 16px; border-width: 0px; font: italic 11px; color: grey ;}")
        
        # grid
        gridVaaka = QGridLayout()
        gridVaaka.setSpacing(10)
        vaakataso.setLayout(gridVaaka)
        
        gridVaaka.addWidget(vaakaLabel, 0, 0, 1, 5)
        gridVaaka.addWidget(vaakafill, 1, 0, 1, 5)
        
        gridVaaka.addWidget(lbl5, 2, 0)
        gridVaaka.addWidget(lbl6, 3, 0)

        gridVaaka.addWidget(self.sld5, 2, 1)
        gridVaaka.addWidget(self.sld6, 3, 1)
        
        gridVaaka.addWidget(lcd5, 2, 2)
        gridVaaka.addWidget(lcd6, 3, 2)
        
        gridVaaka.addWidget(ResetH, 2, 3)
        gridVaaka.addWidget(ResetT, 3, 3)
        
        gridVaaka.addWidget(self.skaala3, 3, 4)
        
        ################################################################
        
        """ TRIGGER & MODE """
        
        # ikkuna
        trigger = QLabel()
        trigger.setMinimumSize(172, 172)
        trigger.setFrameStyle(6)
        trigger.setLineWidth(1)
        trigger.setAutoFillBackground(True)
        trigger.setStyleSheet("QLabel {border-style: outset; border-width: 2px; border-radius: 15px; border-color: black; background-color: rgb(249, 249, 250)}")
        
        # label
        triggerLabel = QLabel()
        triggerLabel.setText("TRIGGER LEVEL")
        triggerLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        triggerLabel.setStyleSheet(".QLabel {max-height: 16px; border-width: 0px; font: bold 14px;}")
        triggerLabel.setStatusTip('Trigger level settings')
        
        # label source
        triggersourcelabel = QLabel()
        triggersourcelabel.setText("TRIGGER SOURCE")
        triggersourcelabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        triggersourcelabel.setStyleSheet(".QLabel {max-height: 16px; border-width: 0px; font: bold 14px;}")
        triggersourcelabel.setStatusTip('Trigger source settings')
        
        # label mode
        modeLabel = QLabel()
        modeLabel.setText("MODE")
        modeLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        modeLabel.setStyleSheet(".QLabel {max-height: 16px; border-width: 0px; font: bold 14px;}")
        modeLabel.setStatusTip('Mode selection')
        
        # trigger source
        self.triggersource = QComboBox()   
        self.triggersource.addItems(["Channel 1", "External"])
        self.triggersource.setCurrentIndex(0)  
        self.triggersource.setStyleSheet(".QComboBox {font: bold 12px;}") #min-height: 25px;
        self.triggersource.setStatusTip('Choose trigger source')
        self.triggersource.currentIndexChanged[int].connect(self.triggerChanged)
        
        # mode
        mode1 = QPushButton('Normal', self)
        mode2 = QPushButton('XY', self)
        
        mode1.setStyleSheet(".QPushButton {font: bold 12px; min-height: 25}")
        mode2.setStyleSheet(".QPushButton {font: bold 12px; min-height: 25}")
        
        mode1.setCheckable(True)
        mode2.setCheckable(True)
        
        mode1.setChecked(True)
        
        mode1.setAutoExclusive(True)
        mode2.setAutoExclusive(True)
        
        mode1.clicked[bool].connect(self.mode1)
        mode2.clicked[bool].connect(self.mode2)
        
        # dial
        self.TriggerDial = QDial()
        self.TriggerDial.setNotchesVisible(True)
        self.TriggerDial.setRange(0,100)
        self.TriggerDial.setValue(1)
        self.TriggerDial.setStatusTip('Trigger level')
        
        self.TriggerDiallcd = QLCDNumber(self)
        self.TriggerDiallcd.setSegmentStyle(2)
        self.TriggerDiallcd.setFixedSize(70,30)
        
        self.TriggerDiallcd.display(self.TriggerDial.value())
        self.TriggerDial.valueChanged.connect(self.TriggerDiallcd.display)
        self.TriggerDial.valueChanged[int].connect(self.triggerlevelChange)
        
        # trigger file label
        self.triggerfilelabel = QLabel()
        self.triggerfilelabel.setMaximumWidth(160)
        self.triggerfilelabel.setWordWrap(True)
        self.triggerfilelabel.setText("")
        self.triggerfilelabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.triggerfilelabel.setStyleSheet(".QLabel {max-height: 50px; border-width: 0px; font: italic 14px; color: darkRed }")
        
        # reset
        btn7 = QPushButton('Reset', self)
        btn7.setFixedSize(50,30)
        btn7.clicked.connect(self.button7Event)
        btn7.setStatusTip('Reset to default value')
        btn7.setStyleSheet("QPushButton { background-color: red; border-style: outset; "\
                                "border-width: 2px; border-radius: 8px; border-color: grey; font: bold 10px;}" \
                                "QPushButton:pressed {background-color: rgb(160, 0, 0); border-style: inset;}")
         
        # grid
        TriggerGrid = QGridLayout()
        TriggerGrid.setSpacing(10)
        trigger.setLayout(TriggerGrid)
        
        TriggerGrid.addWidget(triggerLabel, 0, 0, 1, 4)
        TriggerGrid.addWidget(self.TriggerDiallcd, 1, 0, 1, 2)
        TriggerGrid.addWidget(btn7, 1, 2, 1, 2)
        TriggerGrid.addWidget(self.TriggerSkaala, 2, 0, 1, 4)
        TriggerGrid.addWidget(self.TriggerDial, 3, 0, 1, 4)
        
        TriggerGrid.addWidget(triggersourcelabel, 5, 0, 1, 4)
        TriggerGrid.addWidget(self.triggersource, 6, 0, 1, 4)
        TriggerGrid.addWidget(self.triggerfilelabel, 8, 0, 1, 4)
        
        
        TriggerGrid.addWidget(modeLabel, 9, 0, 1, 4)
        TriggerGrid.addWidget(mode1, 10, 0, 1, 2)
        TriggerGrid.addWidget(mode2, 10, 2, 1, 2)
        
        ################################################################
        
        """ START NAPPI """
        
        # ikkuna
        ohjaus = QLabel()
        ohjaus.setMinimumSize(100, 100)
        ohjaus.setFrameStyle(6)
        ohjaus.setLineWidth(1)
        ohjaus.setAutoFillBackground(True)
        ohjaus.setStyleSheet("QLabel {border-style: outset; border-width: 0px; border-radius: 15px; border-color: black;}")
        
        # nappi
        nappi = QPushButton("START \n STOP", self)
        nappi.setFixedSize(120,120)
        nappi.setStyleSheet(""" .QPushButton {
                                    background-color: red;
                                    border-style: outset;
                                    border-width: 6px;
                                    border-radius: 60px;
                                    border-color: grey;
                                    font: bold 18px; 
                                    }
                                QPushButton:pressed {
                                    background-color: rgb(224, 0, 0);
                                    border-style: inset; }
                                """)
        
        nappi.clicked.connect(self.start)
        nappi.setStatusTip('Start or stop oscilloscope. Keyboard shortcut = space.')
       
        # grid
        ohjausGrid = QGridLayout()
        ohjausGrid.setSpacing(10)
        ohjaus.setLayout(ohjausGrid)
        
        ohjausGrid.addWidget(nappi, 0, 0) 
    
        ################################################################
        
        """ MENU """
        
        about = QAction(QIcon('Media/about.png'), 'About', self)
        about.setShortcut('Ctrl+I')
        about.setStatusTip('About this application')
        about.triggered.connect(self.aboutEvent)
        
        exitAction = QAction(QIcon('Media/exit.png'), '&Exit', self)
        exitAction.setShortcut('Escape')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close) 
        
        openFile = QAction(QIcon('Media/open.png'), 'Open file', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open channel 1 signal file')
        openFile.triggered.connect(self.OpenCh1)
        
        openFile2 = QAction(QIcon('Media/open.png'), 'Open file', self)
        openFile2.setShortcut('Ctrl+P')
        openFile2.setStatusTip('Open channel 2 signal file')
        openFile2.triggered.connect(self.OpenCh2)
        
        chooseColor = QAction(QIcon('Media/color.png'),'Draw color', self)
        chooseColor.setShortcut('Ctrl+U')
        chooseColor.setStatusTip('Choose signal 1 draw color')
        chooseColor.triggered.connect(self.showColorDialog)
        
        chooseColor2 = QAction(QIcon('Media/color.png'),'Draw color', self)
        chooseColor2.setShortcut('Ctrl+J')
        chooseColor2.setStatusTip('Choose signal 2 draw color')
        chooseColor2.triggered.connect(self.showColorDialog2)
        
        LinkVoltages = QAction('Link voltages', self)
        LinkVoltages.setCheckable(True)
        LinkVoltages.setShortcut('Ctrl+G')
        LinkVoltages.setStatusTip('Link channel 2 controls to follow channel 1')
        LinkVoltages.toggled.connect(self.linkVoltages)
        
        chooseBGColor = QAction(QIcon('Media/color.png'),'Background color', self)
        chooseBGColor.setShortcut('Ctrl+B')
        chooseBGColor.setStatusTip('Choose display background color')
        chooseBGColor.triggered.connect(self.ikkuna.showBackgroundColorDialog)
        
        openTriggerFile = QAction(QIcon('Media/open.png'), 'Open file', self)
        openTriggerFile.setShortcut('Ctrl+T')
        openTriggerFile.setStatusTip('Open external trigger signal file')
        openTriggerFile.triggered.connect(self.openTriggerFileDialog)
        
        GridSize = QMenu('Grid size', self)
        GridSize.setStatusTip('Set the display grid size')
        
        GridSizeGroup = QActionGroup(self)
        GridSize1 = QAction('48 px', self)
        GridSize2 = QAction('96 px', self)
        
        GridSize1.setCheckable(True)
        GridSize2.setCheckable(True)
        
        GridSize1.setChecked(True)
        
        GridSize1.setStatusTip('Set the displayed grid size. Does not affect scaling!')
        GridSize2.setStatusTip('Set the displayed grid size. Does not affect scaling!')
        
        GridSizeGroup.addAction(GridSize1)
        GridSizeGroup.addAction(GridSize2)
        
        GridSize.addAction(GridSize1)
        GridSize.addAction(GridSize2)
        GridSize1.triggered.connect(self.setGridSize1)
        GridSize2.triggered.connect(self.setGridSize2)
        
        speedMenu = QMenu('Draw speed', self)
        speedMenu.setStatusTip('Choose refresh speed when using internal triggering.')
        
        speedGroup = QActionGroup(self)
        speed1 = QAction('1/100', self)
        speed2 = QAction('1/10', self)
        speed3 = QAction('1/2', self)
        speed4 = QAction('1', self)
        speed5 = QAction('2', self)
        
        speed1.setCheckable(True)
        speed2.setCheckable(True)
        speed3.setCheckable(True)
        speed4.setCheckable(True)
        speed5.setCheckable(True)

        speed4.setChecked(True)
        
        speed1.setStatusTip('Choose signal refresh speed when using internal triggering. 1 = real-time.')
        speed2.setStatusTip('Choose signal refresh speed when using internal triggering. 1 = real-time.')
        speed3.setStatusTip('Choose signal refresh speed when using internal triggering. 1 = real-time.')
        speed4.setStatusTip('Choose signal refresh speed when using internal triggering. 1 = real-time.')
        speed5.setStatusTip('Choose signal refresh speed when using internal triggering. 1 = real-time.')
        
        speedGroup.addAction(speed1)
        speedGroup.addAction(speed2)
        speedGroup.addAction(speed3)
        speedGroup.addAction(speed4)
        speedGroup.addAction(speed5)

        speedMenu.addAction(speed1)
        speedMenu.addAction(speed2)
        speedMenu.addAction(speed3)
        speedMenu.addAction(speed4)
        speedMenu.addAction(speed5)
        speed1.triggered.connect(self.setSpeed1)
        speed2.triggered.connect(self.setSpeed2)
        speed3.triggered.connect(self.setSpeed3)
        speed4.triggered.connect(self.setSpeed4)
        speed5.triggered.connect(self.setSpeed5)
        
        menubar = QMenuBar()
        
        fileMenu = menubar.addMenu('&Oscilloscope')
        fileMenu.addAction(about)
        fileMenu.addAction(exitAction)
        
        channel1Menu = menubar.addMenu('&Channel 1')
        channel1Menu.addAction(openFile)
        channel1Menu.addAction(chooseColor)
        channel1Menu.addAction(LinkVoltages)
        
        channel2Menu = menubar.addMenu('&Channel 2')
        channel2Menu.addAction(openFile2)  
        channel2Menu.addAction(chooseColor2)
        
        triggerMenu = menubar.addMenu('&Trigger')
        triggerMenu.addAction(openTriggerFile)
        
        viewMenu = menubar.addMenu('&Display')
        viewMenu.addAction(chooseBGColor)
        viewMenu.addMenu(GridSize)
        viewMenu.addMenu(speedMenu)
        
        
        
        ################################################################
         
        """ MAIN GRID """

        grid = QGridLayout()
        grid.setSpacing(10)
        
        grid.setMenuBar(menubar)
        grid.addWidget(self.ikkuna, 0, 0, 1, 3)
        grid.addWidget(trigger, 0, 3, 1, 1)
        grid.addWidget(channel1, 1, 0, 1, 1)
        grid.addWidget(channel2, 1, 1, 1, 1)
        grid.addWidget(vaakataso, 1, 2, 1, 1)
        grid.addWidget(ohjaus, 1, 3, 1, 1)
        
        # Koko grid keski-ikkunan widgettiin
        self.dock.setLayout(grid)
        
        self.show()
       
    def start(self):
        """ START NAPPI """
        if self.settings.on == True:
            self.settings.on = False
            self.statusBar.showMessage("Oscilloscope stopped!")
            self.ikkuna.index = 0
            self.Kanava1.index = 0
            self.Kanava2.index = 0
            self.trigger.index = 0
        else:
            self.settings.on = True
            self.statusBar.showMessage("Oscilloscope started!")
            self.ikkuna.time = timer() # aloitusaika

        self.ikkuna.update()
              
    def changeValue1(self, value):   
        self.Kanava1.ypos = 48*value//10
        self.ikkuna.update()
        
    def changeValue2(self, value): 
        self.Kanava1.voltage = value
        if self.VoltageLink == True:
            self.Kanava2.voltage = value
        self.ikkuna.update()
    
    def changeValue3(self, value):  
        self.Kanava2.ypos = 48*value//10  
        self.ikkuna.update()
        
    def changeValue4(self, value):  
        self.Kanava2.voltage = value
        self.ikkuna.update()  
        
    def changeValue5(self, value):  
        self.settings.xpos = (48*value)//10
        self.ikkuna.update()
                      
    def changeValue6(self, value):  
        self.settings.time = value
        self.ikkuna.update()
        
    def button1Event(self):    
        self.sld1.setValue(0)

    def button2Event(self):    
        self.sld2.setValue(1)   
        self.skaala1.setCurrentIndex(3) 
    
    def button3Event(self):    
        self.sld3.setValue(0)
        
    def button4Event(self):    
        self.sld4.setValue(1)
        self.skaala2.setCurrentIndex(3)
        
    def button5Event(self):    
        self.sld5.setValue(0)    
    
    def button6Event(self):    
        self.sld6.setValue(1)
        self.skaala3.setCurrentIndex(0)    
        
    # Trigger reset    
    def button7Event(self):    
        self.TriggerDial.setValue(1)
        self.TriggerSkaala.setCurrentIndex(0)       
        
    def skaala1changed(self, index):
        if index == 0:
            self.Kanava1.scale = 0.001
        if index == 1:
            self.Kanava1.scale = 0.01
        if index == 2:
            self.Kanava1.scale = 0.1
        if index == 3:
            self.Kanava1.scale = 1
            
        if self.VoltageLink == True:
            self.Kanava2.scale = self.Kanava1.scale   
        self.ikkuna.update()
             
    def skaala2changed(self, index):
        if index == 0:
            self.Kanava2.scale = 0.001
        if index == 1:
            self.Kanava2.scale = 0.01
        if index == 2:
            self.Kanava2.scale = 0.1
        if index == 3:
            self.Kanava2.scale = 1
        self.ikkuna.update()
        
    def skaala3changed(self, index):
        if index == 0:
            self.settings.TimeScale = 1
        if index == 1:
            self.settings.TimeScale = 10
        self.ikkuna.update() 
        
    def linkVoltages(self, toggled): 
        if toggled == True:
            self.VoltageLink = True
            self.Kanava2.scale = self.Kanava1.scale
            self.Kanava2.voltage = self.Kanava1.voltage
            
            self.sld4.setEnabled(False)
            self.skaala2.setEnabled(False)

        else:
            self.VoltageLink = False
            self.sld4.setEnabled(True)
            self.skaala2.setEnabled(True)
            self.Kanava2.voltage = self.sld4.value()
            self.Kanava2.scale = 10**(-1*(3-self.skaala2.currentIndex()))
        
    def triggerlevelChange(self, value):
        self.trigger.voltage = value
    
    def TriggerSkaalachanged(self, index):
        if index == 0:
            self.trigger.scale = 0.001
        if index == 1:
            self.trigger.scale = 0.01
        if index == 2:
            self.trigger.scale = 0.1
        if index == 3:
            self.trigger.scale = 1
        self.ikkuna.update()
    
    def triggerChanged(self, index):
        if index == 0:
            self.trigger.state = False
            self.TriggerDial.setEnabled(True)
            self.TriggerSkaala.setEnabled(True) 
        if index == 1:
            if self.trigger.signal == None:
                self.triggersource.setCurrentIndex(0)
                QMessageBox.warning(self, "Error!", "External trigger signal file missing!\n\nLoad trigger file and try again.")
            else:    
                self.trigger.state = True
                self.TriggerDial.setEnabled(False)
                self.TriggerSkaala.setEnabled(False)  
        
    def mode1(self):
        self.settings.mode = "normal"
        self.OnOff1.setEnabled(True)
        self.OnOff2.setEnabled(True)
        self.TriggerDial.setEnabled(True)
        self.triggersource.setEnabled(True)
        self.TriggerSkaala.setEnabled(True) 
            
    def mode2(self):
        self.settings.mode = "XY"
        
        # molemmat kanavat päälle
        self.OnOff1.setChecked(True) 
        self.OnOff2.setChecked(True)    
        
        # disabloidaan osa elementeistä koska niillä ei ole mitään funktiota tässä moodissa.  
        self.OnOff1.setEnabled(False)
        self.OnOff2.setEnabled(False)     
        self.TriggerDial.setEnabled(False)
        self.triggersource.setEnabled(False)
        self.TriggerSkaala.setEnabled(False)  
        
    def setSpeed1(self):
        self.ikkuna.speed = 1/100
    def setSpeed2(self):
        self.ikkuna.speed = 1/10
    def setSpeed3(self):
        self.ikkuna.speed = 1/2
    def setSpeed4(self):
        self.ikkuna.speed = 1    
    def setSpeed5(self):
        self.ikkuna.speed = 2            
        
    def OpenCh1(self):
        try:
            fname = QFileDialog.getOpenFileName(self, 'Open file')
            file = fname[0]
            if self.Kanava1.ReadFile(file):
                self.Ch1filelabel.setText(file.split("/")[-1])
                self.Kanava1.index = 0 # nollataan index
                self.ikkuna.index = 0
        except ValueError:
            QMessageBox.warning(self, "File error", "Value error!\n\nSignal file could not be read.")
        except OSError:
            QMessageBox.warning(self, "File error", "File error!\n\nCould not open file \"{}\".".format(file.split("/")[-1]))  
        except RuntimeError:
            QMessageBox.warning(self, "File error", "File error!\n\nSignal file is too short (under 1 second).")
        except SyntaxError:
            QMessageBox.warning(self, "File error", "Bit depth error!\n\nOnly 16 bit WAV files are supported.")
        except NameError:
            QMessageBox.warning(self, "File error", "Too many channels!\n\nOnly mono files are supported.")
        except TypeError:
            QMessageBox.warning(self, "File error", "Format error!\n\nWrong file format \"{}\".\nSupported file formats are CVS and WAV.".format(file.split(".")[-1]))        

    def OpenCh2(self):
        try:
            fname = QFileDialog.getOpenFileName(self, 'Open file')
            file = fname[0]
            if self.Kanava2.ReadFile(file):
                self.Ch2filelabel.setText(file.split("/")[-1])
                self.Kanava2.index = 0 
                self.ikkuna.index = 0
        except ValueError:
            QMessageBox.warning(self, "File error", "Value error!\n\nSignal file could not be read.")
        except OSError:
            QMessageBox.warning(self, "File error", "File error!\n\nCould not open file \"{}\".".format(file.split("/")[-1]))  
        except RuntimeError:
            QMessageBox.warning(self, "File error", "File error!\n\nSignal file is too short (under 1 second).")
        except SyntaxError:
            QMessageBox.warning(self, "File error", "Bit depth error!\n\nOnly 16 bit WAV files are supported.")
        except NameError:
            QMessageBox.warning(self, "File error", "Too many channels!\n\nOnly mono files are supported.")
        except TypeError:
            QMessageBox.warning(self, "File error", "Format error!\n\nWrong file format \"{}\".\nSupported file formats are CVS and WAV.".format(file.split(".")[-1]))
     
    def openTriggerFileDialog(self): 
        try:
            fname = QFileDialog.getOpenFileName(self, 'Open file')
            file = fname[0]
            if self.trigger.ReadFile(file):
                self.triggerfilelabel.setText(file.split("/")[-1])
                self.trigger.index = 0 
        except ValueError:
            QMessageBox.warning(self, "File error", "Value error!\n\nSignal file could not be read.")
        except OSError:
            QMessageBox.warning(self, "File error", "File error!\n\nCould not open file \"{}\".".format(file.split("/")[-1]))  
        except RuntimeError:
            QMessageBox.warning(self, "File error", "File error!\n\nSignal file is too short (under 1 second).")
        except SyntaxError:
            QMessageBox.warning(self, "File error", "Bit depth error!\n\nOnly 16 bit WAV files are supported.")
        except NameError:
            QMessageBox.warning(self, "File error", "Too many channels!\n\nOnly mono files are supported.")
        except TypeError:
            QMessageBox.warning(self, "File error", "Format error!\n\nWrong file format \"{}\".\nSupported file formats are CVS and WAV.".format(file.split(".")[-1]))
            
    def Channel1StateChange(self, state):
        if state == Qt.Checked:
            self.Kanava1.state = True
        else:
            self.Kanava1.state = False
        self.ikkuna.update()    
            
    def Channel2StateChange(self, state):
        if state == Qt.Checked:
            self.Kanava2.state = True
        else:
            self.Kanava2.state = False
        self.ikkuna.update()  
                    
    def showColorDialog(self): 
        self.Kanava1.drawColor = QColorDialog.getColor()
        self.ikkuna.update()
        
    def showColorDialog2(self): 
        self.Kanava2.drawColor = QColorDialog.getColor()   
        self.ikkuna.update()
        
    def setGridSize1(self):
        self.ikkuna.grid = 48 
        self.ikkuna.update()  
        
    def setGridSize2(self):
        self.ikkuna.grid = 96 
        self.ikkuna.update()         

    def keyPressEvent(self, e):

        if e.key() == QtCore.Qt.Key_Space:
            self.start()
        
        # debug tulostuksia...
        if e.key() == QtCore.Qt.Key_P: 
            print("Ikkunan koko: ", self.width()," * ", self.height(), "\n")
            
        if e.key() == QtCore.Qt.Key_K: 
            self.Kanava1.PrintInfo()
            
        if e.key() == QtCore.Qt.Key_L:
            self.Kanava2.PrintInfo()
            
        if e.key() == QtCore.Qt.Key_J:
            self.settings.PrintInfo()
            
        if e.key() == QtCore.Qt.Key_T:
            self.trigger.PrintInfo()
            
        if e.key() == QtCore.Qt.Key_A:
            print("Time: ", self.ikkuna.time, " ; ", timer(), " ; ", timer()-self.ikkuna.time, "\n")
            
        if e.key() == QtCore.Qt.Key_X:
            print("Speed:", self.ikkuna.speed)   
            
    def center(self):
        # keskitetään ikkuna näytöllä
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        #print("Desktop resolution: ", screen)
        self.move((screen.width()-size.width())/2, 
            (screen.height()-size.height())/2)
        
    def closeEvent(self, event):  
        reply = QMessageBox.question(self,"Exit",
            "So you wanna quit?", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()  
            
    def aboutEvent(self, event):
        
        QMessageBox.about(self, "About", """        CSE-A1121 
        Ohjelmoinnin peruskurssi Y2 
        Kevät/kesä 2015 
                
        Projektityö: Oskilloskooppi 
                                                    
        Juri Lukkarila 
        81915H
        
        """ + "Python {:}, QT {:}, PyQT {:}".format(sys.version.split(" ")[0], QT_VERSION_STR, PYQT_VERSION_STR))
        
#################################################################################################################    
                
if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = Oscilloscope()
    sys.exit(app.exec_())