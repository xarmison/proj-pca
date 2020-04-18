from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QFileDialog
from PyQt5 import QtCore, QtGui, QtWidgets
from os import path
import numpy as np
import cv2 as cv
import sys

class DisplayImageWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(DisplayImageWidget, self).__init__(parent)

        self.image_frame = QtWidgets.QLabel()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.image_frame)
        self.setLayout(self.layout)

        self.set_frame(cv.imread('./icons/placeholder.png'))
    
    def set_frame(self, image):

        height, width, _ = image.shape

        if (height < 660 or width < 1091):
            padding_height = max(660 - height, 0)//2
            padding_width = max(1091 - width, 0)//2
            
            image = cv.copyMakeBorder(
                image, 
                padding_height, padding_height, 
                padding_width, padding_width, 
                cv.BORDER_CONSTANT
            )
        else:
            image = cv.resize(image, (1091, 660))

        height, width, _ = image.shape
        bytesPerLine = 3 * width
        
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)  
        image = QtGui.QImage(image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        self.image_frame.setPixmap(QtGui.QPixmap.fromImage(image))

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Internal variables
        self.video_file_name = ''
        self.options = {
            'log_speed': False,
            'draw_axis': False,
            'color_mask': False,
            'save_video': False,
            'log_position': False,
            'frame_rate': 30,
            'lower_boundary': 100,
            'upper_boundary': 160
        }
        
        self.setupUi(self)
        self.show()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 720)
        MainWindow.setWindowIcon(QtGui.QIcon('icons/app_icon.png'))

        self.allFather = QtWidgets.QWidget(MainWindow)
        self.allFather.setObjectName("allFather")

        self.gridLayout = QtWidgets.QGridLayout(self.allFather)
        self.gridLayout.setObjectName("gridLayout")
        
        self.frame = DisplayImageWidget(self.allFather)
        self.frame.setMinimumSize(QtCore.QSize(1091, 660))
        self.frame.setObjectName('frame')
        self.gridLayout.addWidget(self.frame, 1, 0, 1, 1)

        # self.graphicsView = QtWidgets.QGraphicsView(self.allFather)
        # self.graphicsView.setObjectName("graphicsView")
        # self.gridLayout.addWidget(self.graphicsView, 1, 0, 1, 1)
        
        self.sideBar = QtWidgets.QVBoxLayout()
        self.sideBar.setObjectName("sideBar")
        
        # Checkbozes for optional settings
        self.opitionalSettings = QtWidgets.QGridLayout()
        self.opitionalSettings.setObjectName("opitionalSettings")
        
        self.drawAxis = QtWidgets.QCheckBox(self.allFather)
        self.drawAxis.setObjectName("drawAxis")
        self.drawAxis.stateChanged.connect(lambda: self.change_options('draw_axis'))
        self.opitionalSettings.addWidget(self.drawAxis, 3, 0, 1, 1)
        
        self.logPosition = QtWidgets.QCheckBox(self.allFather)
        self.logPosition.setObjectName("logPosition")
        self.logPosition.stateChanged.connect(lambda: self.change_options('log_position'))
        self.opitionalSettings.addWidget(self.logPosition, 4, 0, 1, 1)
        
        self.logSpeed = QtWidgets.QCheckBox(self.allFather)
        self.logSpeed.setObjectName("logSpeed")
        self.logSpeed.stateChanged.connect(lambda: self.change_options('log_speed'))
        self.opitionalSettings.addWidget(self.logSpeed, 5, 0, 1, 1)
        
        self.label_2 = QtWidgets.QLabel(self.allFather)
        self.label_2.setObjectName("label_2")
        self.opitionalSettings.addWidget(self.label_2, 1, 0, 1, 1)
        
        self.colorMask = QtWidgets.QCheckBox(self.allFather)
        self.colorMask.setObjectName("colorMask")
        self.colorMask.stateChanged.connect(lambda: self.change_options('color_mask'))
        self.opitionalSettings.addWidget(self.colorMask, 6, 0, 1, 1)
        
        self.saveVideo = QtWidgets.QCheckBox(self.allFather)
        self.saveVideo.setObjectName("saveVideo")
        self.saveVideo.stateChanged.connect(lambda: self.change_options('save_video'))
        self.opitionalSettings.addWidget(self.saveVideo, 7, 0, 1, 1)
        
        self.line = QtWidgets.QFrame(self.allFather)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.opitionalSettings.addWidget(self.line, 2, 0, 1, 1)
        
        self.sideBar.addLayout(self.opitionalSettings)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, 
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Expanding
        )
        self.sideBar.addItem(spacerItem)
        
        # Frame rate input
        self.frameRate = QtWidgets.QGridLayout()
        self.frameRate.setObjectName("frameRate")
        
        self.frBtn = QtWidgets.QPushButton(self.allFather)
        self.frBtn.setObjectName("frBtn")
        self.frBtn.clicked.connect(self.change_frame_rate)
        self.frameRate.addWidget(self.frBtn, 6, 0, 1, 1)
        
        self.inputedFrameRate = QtWidgets.QSpinBox(self.allFather)
        self.inputedFrameRate.setMaximum(99999)
        self.inputedFrameRate.setProperty("value", 30)
        self.inputedFrameRate.setObjectName("inputedFrameRate")
        self.frameRate.addWidget(self.inputedFrameRate, 5, 0, 1, 1)
        
        self.label_1 = QtWidgets.QLabel(self.allFather)
        self.label_1.setObjectName("label_1")
        self.frameRate.addWidget(self.label_1, 3, 0, 1, 1)
        
        self.line_2 = QtWidgets.QFrame(self.allFather)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.frameRate.addWidget(self.line_2, 4, 0, 1, 1)
        
        self.sideBar.addLayout(self.frameRate)
        spacerItem1 = QtWidgets.QSpacerItem(
            20, 40, 
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Expanding
        )
        self.sideBar.addItem(spacerItem1)
        
        # input for the color boundaties
        self.colorSettings = QtWidgets.QGridLayout()
        self.colorSettings.setObjectName("colorSettings")
        
        self.colorLabel = QtWidgets.QLabel(self.allFather)
        self.colorLabel.setObjectName("colorLabel")
        self.colorSettings.addWidget(self.colorLabel, 1, 0, 1, 1)
        
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        
        self.lowerBoundaryLabel = QtWidgets.QLabel(self.allFather)
        self.lowerBoundaryLabel.setObjectName("lowerBoundaryLabel")
        self.horizontalLayout_2.addWidget(self.lowerBoundaryLabel)
        
        self.lowerBoundary = QtWidgets.QSpinBox(self.allFather)
        self.lowerBoundary.setMaximum(255)
        self.lowerBoundary.setProperty("value", 100)
        self.lowerBoundary.setObjectName("lowerBoundary")
        
        self.horizontalLayout_2.addWidget(self.lowerBoundary)
        self.colorSettings.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)
        
        self.colorSettingsBtn = QtWidgets.QPushButton(self.allFather)
        self.colorSettingsBtn.setObjectName("colorSettingsBtn")
        self.colorSettingsBtn.clicked.connect(self.change_boundaries)
        self.colorSettings.addWidget(self.colorSettingsBtn, 4, 0, 1, 1)
        
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        
        self.upperBoundaryLabel = QtWidgets.QLabel(self.allFather)
        self.upperBoundaryLabel.setObjectName("upperBoundaryLabel")
        self.horizontalLayout_3.addWidget(self.upperBoundaryLabel)
        
        self.upperBoundary = QtWidgets.QSpinBox(self.allFather)
        self.upperBoundary.setMaximum(255)
        self.upperBoundary.setProperty("value", 160)
        self.upperBoundary.setObjectName("upperBoundary")
        self.horizontalLayout_3.addWidget(self.upperBoundary)
        self.colorSettings.addLayout(self.horizontalLayout_3, 3, 0, 1, 1)
        
        self.sideBar.addLayout(self.colorSettings)
        spacerItem2 = QtWidgets.QSpacerItem(
            20, 40, 
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Expanding
        )
        self.sideBar.addItem(spacerItem2)
        
        self.mainBtns = QtWidgets.QGridLayout()
        self.mainBtns.setObjectName("mainBtns")

        self.startBtn = QtWidgets.QPushButton(self.allFather)
        self.startBtn.setObjectName("startBtn")
        self.startBtn.clicked.connect(self.start)
        self.mainBtns.addWidget(self.startBtn, 1, 0, 1, 1)
        
        self.playBtn = QtWidgets.QPushButton(self.allFather)
        self.playBtn.setObjectName("playBtn")
        self.playBtn.clicked.connect(self.play_pause)
        self.mainBtns.addWidget(self.playBtn, 2, 0, 1, 1)
        
        self.sideBar.addLayout(self.mainBtns)
        self.gridLayout.addLayout(self.sideBar, 1, 1, 1, 1)
        
        MainWindow.setCentralWidget(self.allFather)
        
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1280, 25))
        self.menubar.setObjectName("menubar")
        
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        
        MainWindow.setMenuBar(self.menubar)
        
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        
        MainWindow.setStatusBar(self.statusbar)
        
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionExit.triggered.connect(self.exit)
        
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionOpen.triggered.connect(self.open_file)
        
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Mice Tracker"))

        self.drawAxis.setText(_translate("MainWindow", "Draw Axis"))
        self.drawAxis.setToolTip(_translate(
            "MainWindow", "Draws both axis found through PCA. "
        ))
        
        self.logPosition.setText(_translate("MainWindow", "Log Position"))
        self.logPosition.setToolTip(_translate(
            "MainWindow", "Creates a log file with the (x, y) position\
            coordinates of the tracked animal."
        ))
        
        self.logSpeed.setText(_translate("MainWindow", "Log Speed"))
        self.logSpeed.setToolTip(_translate(
            "MainWindow", "Creates a log file with the speed of the tracked animal."
        ))
        
        self.label_2.setText(_translate("MainWindow", "Optional Settings"))
        self.label_2.setToolTip(_translate(
            "MainWindow", "Sets the additional settings."
        )
        )
        
        self.colorMask.setText(_translate("MainWindow", "Color Mask"))
        self.colorMask.setToolTip(_translate(
            "MainWindow", "Draws a colored mask over the detection."
        ))
        
        self.saveVideo.setText(_translate("MainWindow", "Save Video"))
        self.saveVideo.setToolTip(_translate(
            "MainWindow", "Creates a video file with the analysis results."
        ))
        
        self.frBtn.setText(_translate("MainWindow", "Change"))
        self.frBtn.setToolTip(_translate("MainWindow", "Applies the change."))
        
        self.label_1.setText(_translate("MainWindow", "Frame Rate"))
        self.label_1.setToolTip(_translate("MainWindow", "Sets the video\'s frame rate."))
        
        self.colorLabel.setText(_translate("MainWindow", "Color Settings"))
        self.colorLabel.setToolTip(_translate(
            "MainWindow", "The color range of the mice in the subtracted image\
            must be adjusted according to the video."
        ))
        
        self.colorSettingsBtn.setToolTip(_translate("MainWindow", "Applies the change."))
        self.lowerBoundaryLabel.setText(_translate("MainWindow", "Lower Boundary"))
        
        self.upperBoundaryLabel.setText(_translate("MainWindow", "Upper Boundary"))
        self.colorSettingsBtn.setText(_translate("MainWindow", "Change"))
        
        self.startBtn.setText(_translate("MainWindow", "Start"))
        self.startBtn.setToolTip(_translate("MainWindow", "Initiate tracking."))

        self.playBtn.setText(_translate("MainWindow", "Play/Pause"))
        self.playBtn.setToolTip(_translate("MainWindow", "Resumes or pause the video stream."))
        
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        
        self.actionExit.setStatusTip(_translate("MainWindow", "Close application"))
        self.actionExit.setToolTip(_translate("MainWindow", "Close application"))
        
        self.actionExit.setShortcut(_translate("MainWindow", "Ctrl+Q"))
        self.actionExit.setWhatsThis(_translate("MainWindow", "Close application"))
        
        self.actionOpen.setToolTip(_translate("MainWindow", "Open video file for analysis"))
        self.actionOpen.setText(_translate("MainWindow", "Open Video"))
        self.actionOpen.setShortcut(_translate("MainWindow", "Ctrl+O"))

    def exit(self):
        choice = QtWidgets.QMessageBox.question(
            self, 'Exit Application', 'Are you sure ?', 
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()

    def open_file(self):
        self.video_file_name, _ = QFileDialog.getOpenFileName(self)

    def change_options(self, option):
        self.options[option] =  not self.options[option] 

    def change_frame_rate(self):
        self.options['frame_rate'] = self.inputedFrameRate.value()

    def change_boundaries(self):
        self.options['lower_boundary'] = self.lowerBoundary.value()
        self.options['upper_boundary'] = self.upperBoundary.value()

    def start(self):
        print('Start video stream')
        
    def play_pause(self):
        print('play/pause')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MainWindow()

    sys.exit(app.exec_())