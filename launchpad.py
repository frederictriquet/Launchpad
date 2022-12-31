from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
import sys
import json
import vlc

class Launchpad(QtWidgets.QMainWindow):
    def __init__(self, conf):
        # self.load_conf(sys.argv[1])
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle("Launchpad")

        self.instance = vlc.get_default_instance()
        self.media = None
        self.mediaplayer = self.instance.media_player_new()

        self.conf = conf
        self.create_ui(conf)
        self.is_paused = False

        self.current_launched = None

    def create_ui(self, conf):
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        self.playbuttonbox = QtWidgets.QHBoxLayout()
        self.playbutton = {}
        for button in conf:
            b = QtWidgets.QPushButton(button['label'])
            b.setCheckable(True)
            b.clicked[bool].connect(self.launch)
            self.playbuttonbox.addWidget(b)
            self.playbutton[button['label']] = b



        self.topzone = QtWidgets.QHBoxLayout()
        self.topzone.addLayout(self.playbuttonbox)

        self.lowzone = QtWidgets.QVBoxLayout()
        # self.lowzone.addWidget(self.positionslider)
        # self.lowzone.addLayout(self.hbuttonbox)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addLayout(self.topzone)
        self.vboxlayout.addLayout(self.lowzone)
        self.widget.setLayout(self.vboxlayout)

    def launch(self):
        checked = []
        for b in self.conf:
            if self.playbutton[b['label']].isChecked():
                self.playbutton[b['label']].setChecked(False)
                checked.append(b['label'])
        if len(checked) == 0:
            self.current_launched = None
        elif len(checked) == 1:
            self.current_launched = checked[0]
        else:
            if checked[0] == self.current_launched:
                self.current_launched = checked[1]
            else:
                self.current_launched = checked[0]
        if self.current_launched:
            self.playbutton[self.current_launched].setChecked(True)
        self.play_sound(self.current_launched)
    
    def play_sound(self, label):
        print(label)
        if label:
            fullpath = 'Todo'
            self.media = self.instance.media_new(fullpath)
            self.mediaplayer.set_media(self.media)
            if self.mediaplayer.play() == -1:
                self.open_file()
                return
            self.mediaplayer.play()
        else:
            self.mediaplayer.stop()


def load_conf(conffile):
    with open(conffile) as jsonfile:
        stringdata = jsonfile.read()
        return json.loads(stringdata)

def main():
    conf = load_conf(sys.argv[1])
    app = QtWidgets.QApplication(sys.argv)
    launchpad = Launchpad(conf)
    launchpad.show()
    launchpad.resize(800, 600)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
