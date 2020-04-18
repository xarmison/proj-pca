from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QFileDialog
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from utils import getOrientation
from time import sleep
from os import path
import numpy as np
import cv2 as cv
import sys

class FrameProcessor:
    def __init__(self, options):
        self.file_name = None
        self.options = options
        self.set_options(self.options)

        self.lower_white = np.array([self.options['lower_boundary']] * 3)
        self.upper_white = np.array([self.options['upper_boundary']] * 3)

        # Varibles fo tracking the mice's position
        self.previous_pos = (0, 0)
        self.current_pos = (0, 0)

        self.frame_index = 0
        self.traveled_distance = 0

        self.cap = None

    def load_video(self, file_path):
        self.file_name = file_path.split('/')[-1].split('.')[0]

        self.cap = cv.VideoCapture(file_path)
        self.frameWidth = int(self.cap.get(3)) 
        self.frameHeight = int(self.cap.get(4))

        if (not self.cap.isOpened()):
            print('Error opening video stream!')
            exit()

        # First frame as the background image
        ret, self.bg_img = self.cap.read()
        
        if (not ret):
            print('Error readning video stream')
            exit()

    def set_options(self, options):
        if (self.file_name is None):
            return

        self.options = options

        self.lower_white = np.array([self.options['lower_boundary']] * 3)
        self.upper_white = np.array([self.options['upper_boundary']] * 3)

        # Creates a stream object for writing the output
        if (self.options['save_video']):
            result_file_name =  f'./results/{self.file_name}_result.avi'

            self.out_writer = cv.VideoWriter(
                result_file_name,
                cv.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                self.options['frame_rate'], 
                (self.frameWidth, self.frameHeight)
            )

        # Creates a file for position logging
        if (self.options['log_position']):
            self.pos_log_file = f'./results/{self.file_name}_pos.csv'

            if not path.isfile(self.pos_log_file): 
                with open(self.pos_log_file, 'w') as logFile:
                    logFile.write('x,y\n')

        # Creates a file for position logging
        if (self.options['log_speed']):
            self.speed_log_file = f'./results/{self.file_name}_speed.csv'

            if not path.isfile(self.speed_log_file):
                with open(self.speed_log_file, 'w') as logFile:
                    logFile.write('time,speed\n')

    def process_frame(self):
        
        if (self.cap is None):
            print('Load the video file first')

            return None

        ret, frame = self.cap.read()

        if (not ret):
            print('Error readning video stream')
            exit()
        
        sub_frame = cv.absdiff(frame, self.bg_img)
           
        filtered_frame = cv.inRange(sub_frame, self.lower_white, self.upper_white)
        
        # Kernel for morphological operation opening
        kernel3 = cv.getStructuringElement(
            cv.MORPH_ELLIPSE,
            (3, 3),
            (-1, -1)
        )

        kernel20 = cv.getStructuringElement(
            cv.MORPH_ELLIPSE,
            (20, 20),
            (-1, -1)
        )

        # Morphological opening
        mask = cv.dilate(cv.erode(filtered_frame, kernel3), kernel20)

        mask_roi = cv.bitwise_and(sub_frame, sub_frame, mask=mask)

        # Find all the contours in the mask
        returns = cv.findContours(mask, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
        
        # Check what findContours returned
        contours = []
        if (len(returns) == 3):
            contours = returns[1]
        else:
            contours = returns[0]
        
        for i, c in enumerate(contours):
            # Calculate the area of each contour
            area = cv.contourArea(c)

            # Ignore contours that are too small or too large
            if area < 1e2 or 1e5 < area:
                continue

            # Draw each contour only for visualisation purposes
            cv.drawContours(frame, contours, i, (255, 0, 255), 2)

            # Find the orientation of each shape
            self.current_pos, _ = getOrientation(c, frame, self.options['draw_axis'])

        speed = np.sqrt(
            (self.previous_pos[0] - self.current_pos[0])**2 + 
            (self.previous_pos[1] - self.current_pos[1])**2
        )

        self.traveled_distance += speed
        self.previous_pos = self.current_pos

        if (self.options['show_speed']):
            cv.putText(
                frame, f'{speed:.3f}', self.current_pos,
                cv.FONT_HERSHEY_COMPLEX,
                0.5, (255, 255, 255)
            )

        if(self.options['log_speed']):
            if(self.current_pos[0] > 50 and self.current_pos[1] > 50):        
                with open(self.speed_log_file, 'a') as logFile:
                    logFile.write(f'{self.frame_index * (1/float(self.options["frame_rate"])):.3f},{speed:.3f}\n')

        # Save position to file
        if(self.options['log_position']):
            with open(self.pos_log_file, 'a') as logFile:
                if(self.current_pos[0] > 50 and self.current_pos[1] > 50):
                    # Changes the coordinates' center to the bottom left for later plotting
                    logFile.write(f'{self.current_pos[0]},{self.frameHeight - self.current_pos[1]}\n')

        if(self.options['color_mask']):
            # Change the color of the mask
            colored_mask = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
            colored_mask[np.where((colored_mask == [255, 255, 255]).all(axis = 2))] = [222, 70, 222]

            # Apply the mask
            frame = cv.add(frame, colored_mask)        

        self.frame_index += 1
        
        if(self.options['save_video']):
            self.out_writer.write(frame)

        height, width, _ = frame.shape

        if (height < 660 or width < 1091):
            padding_height = max(660 - height, 0)//2
            padding_width = max(1091 - width, 0)//2
            
            frame = cv.copyMakeBorder(
                frame, 
                padding_height, padding_height, 
                padding_width, padding_width, 
                cv.BORDER_CONSTANT
            )
        else:
            frame = cv.resize(frame, (1091, 660))

        return frame

class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, parent=None):
        QThread.__init__(self, parent=parent)       

        self.paused = False

        self.options = {
            'log_speed': False,
            'draw_axis': False,
            'color_mask': False,
            'save_video': False,
            'show_speed': False,
            'log_position': False,
            'lower_boundary': 100,
            'upper_boundary': 160,
            'frame_rate': 30
        }

        self.processor = FrameProcessor(self.options)

        self.set_placeholder()

    def play_pause(self):
        self.paused = not self.paused

    def set_placeholder(self):
        image = cv.imread('./icons/placeholder.png')
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

        height, width, _ = image.shape
        bytesPerLine = 3 * width
        
        convertToQtFormat = QImage(image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
                
        self.changePixmap.emit(convertToQtFormat)

    def run(self):
        while True:
            if  (not self.paused):
                continue

            result = self.processor.process_frame()

            image = cv.cvtColor(result, cv.COLOR_BGR2RGB)

            height, width, _ = image.shape
            bytesPerLine = 3 * width
            
            convertToQtFormat = QImage(image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
                    
            self.changePixmap.emit(convertToQtFormat)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Internal variables
        self.video_file_name = ''
        self.paused = True
        
        self.th = Thread(self)

        self.setupUi(self)

        self.th.changePixmap.connect(self.set_frame)
        self.th.set_placeholder()
        self.th.start()

        self.show()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 720)
        MainWindow.setWindowIcon(QtGui.QIcon('icons/app_icon.png'))

        self.allFather = QtWidgets.QWidget(MainWindow)
        self.allFather.setObjectName("allFather")

        self.gridLayout = QtWidgets.QGridLayout(self.allFather)
        self.gridLayout.setObjectName("gridLayout")
        
        # self.frame = DisplayImageWidget(self.allFather)
        # self.frame.setMinimumSize(QtCore.QSize(1091, 660))
        # self.frame.setObjectName('frame')
        # self.gridLayout.addWidget(self.frame, 1, 0, 1, 1)

        self.image_frame = QtWidgets.QLabel()
        self.image_frame.setObjectName('image_frame')
        self.gridLayout.addWidget(self.image_frame, 1, 0, 1, 1)
        
        self.sideBar = QtWidgets.QVBoxLayout()
        self.sideBar.setObjectName("sideBar")

        self.fileSettings = QtWidgets.QGridLayout()
        self.fileSettings.setObjectName("fileSettings")
        
        self.openFileBtn = QtWidgets.QPushButton(self.allFather)
        self.openFileBtn.setObjectName("openFileBtn")
        self.openFileBtn.clicked.connect(self.open_file)
        self.fileSettings.addWidget(self.openFileBtn, 1, 0, 1, 1)
        
        self.sideBar.addLayout(self.fileSettings)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, 
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Expanding
        )
        self.sideBar.addItem(spacerItem)
        
        # Checkbozes for optional settings
        self.opitionalSettings = QtWidgets.QGridLayout()
        self.opitionalSettings.setObjectName("opitionalSettings")
        
        self.drawAxis = QtWidgets.QCheckBox(self.allFather)
        self.drawAxis.setObjectName("drawAxis")
        self.drawAxis.stateChanged.connect(lambda: self.change_options('draw_axis'))
        self.opitionalSettings.addWidget(self.drawAxis, 4, 0, 1, 1)
        
        self.logSpeed = QtWidgets.QCheckBox(self.allFather)
        self.logSpeed.setObjectName("logSpeed")
        self.logSpeed.stateChanged.connect(lambda: self.change_options('log_speed'))
        self.opitionalSettings.addWidget(self.logSpeed, 8, 0, 1, 1)
        
        self.logPosition = QtWidgets.QCheckBox(self.allFather)
        self.logPosition.setObjectName("logPosition")
        self.logPosition.stateChanged.connect(lambda: self.change_options('log_position'))
        self.opitionalSettings.addWidget(self.logPosition, 7, 0, 1, 1)
        
        self.label_2 = QtWidgets.QLabel(self.allFather)
        self.label_2.setObjectName("label_2")
        self.opitionalSettings.addWidget(self.label_2, 2, 0, 1, 1)
        
        self.saveVideo = QtWidgets.QCheckBox(self.allFather)
        self.saveVideo.setObjectName("saveVideo")
        self.saveVideo.stateChanged.connect(lambda: self.change_options('save_video'))
        self.opitionalSettings.addWidget(self.saveVideo, 10, 0, 1, 1)
        
        self.line = QtWidgets.QFrame(self.allFather)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.opitionalSettings.addWidget(self.line, 3, 0, 1, 1)
        
        self.showSpeed = QtWidgets.QCheckBox(self.allFather)
        self.showSpeed.setObjectName("showSpeed")
        self.showSpeed.stateChanged.connect(lambda: self.change_options('show_speed'))
        self.opitionalSettings.addWidget(self.showSpeed, 5, 0, 1, 1)
        
        self.colorMask = QtWidgets.QCheckBox(self.allFather)
        self.colorMask.setObjectName("colorMask")
        self.colorMask.stateChanged.connect(lambda: self.change_options('color_mask'))
        self.opitionalSettings.addWidget(self.colorMask, 6, 0, 1, 1)
        
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

        self.line_3 = QtWidgets.QFrame(self.allFather)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.colorSettings.addWidget(self.line_3, 2, 0, 1, 1)
        
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
        self.colorSettings.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)
        
        self.colorSettingsBtn = QtWidgets.QPushButton(self.allFather)
        self.colorSettingsBtn.setObjectName("colorSettingsBtn")
        self.colorSettingsBtn.clicked.connect(self.change_boundaries)
        self.colorSettings.addWidget(self.colorSettingsBtn, 5, 0, 1, 1)
        
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
        self.colorSettings.addLayout(self.horizontalLayout_3, 4, 0, 1, 1)
        
        self.sideBar.addLayout(self.colorSettings)
        spacerItem2 = QtWidgets.QSpacerItem(
            20, 40, 
            QtWidgets.QSizePolicy.Minimum, 
            QtWidgets.QSizePolicy.Expanding
        )
        self.sideBar.addItem(spacerItem2)
        
        self.mainBtns = QtWidgets.QGridLayout()
        self.mainBtns.setObjectName("mainBtns")
        
        self.playBtn = QtWidgets.QPushButton(self.allFather)
        self.playBtn.setObjectName("playBtn")
        self.playBtn.clicked.connect(self.th.play_pause)
        self.mainBtns.addWidget(self.playBtn, 1, 0, 1, 1)
        
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
        self.setStatusBar(self.statusbar)
        
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

        self.openFileBtn.setText(_translate("MainWindow", "Open File"))
        self.openFileBtn.setShortcut(_translate("MainWindow", "Ctrl+O"))

        self.drawAxis.setText(_translate("MainWindow", "Draw Axis"))
        self.drawAxis.setToolTip(_translate(
            "MainWindow", "Draws both axis found through PCA. "
        ))

        self.showSpeed.setText(_translate("MainWindow", "Show Speed"))
        self.showSpeed.setToolTip(_translate(
            "MainWindow", "Displays the animal's current speed."
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

        self.th.processor.load_video(self.video_file_name)

        self.statusBar().showMessage('Video loaded!')

    def change_options(self, option):
        self.th.options[option] =  not self.th.options[option] 

        self.th.processor.set_options(self.th.options)

    def change_frame_rate(self):
        self.th.options['frame_rate'] = self.inputedFrameRate.value()

        self.th.processor.set_options(self.th.options)

    def change_boundaries(self):
        self.th.options['lower_boundary'] = self.lowerBoundary.value()
        self.th.options['upper_boundary'] = self.upperBoundary.value()

        self.th.processor.set_options(self.th.options)

    @pyqtSlot(QImage)
    def set_frame(self, frame):
        self.image_frame.setPixmap(QPixmap.fromImage(frame))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MainWindow()

    sys.exit(app.exec_())