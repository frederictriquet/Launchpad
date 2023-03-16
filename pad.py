import os
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
import sys
import json
import vlc
import math
from datetime import datetime

NB_ROW_MAX = 20

class Launchpad(QtWidgets.QMainWindow):
  def __init__(self):
    conf_file = './conf.json'
    if len(sys.argv) == 2:
      conf_file = sys.argv[1]
    self.load_conf(conf_file)
    QtWidgets.QMainWindow.__init__(self)
    self.setWindowTitle("Launchpad")
    self.setWindowIcon(QtGui.QIcon('icon.png'))
    self.kbd = "AZERTYUIOPQSDFGHJKLMWXCVBN"
    # self.setWindowIconText("FRED")
    # self.setStyleSheet("""
    # background: blue
    # """)

    self.instance = vlc.get_default_instance()
    self.media = None
    self.mediaplayer = self.instance.media_player_new()

    self.create_ui()
    self.is_paused = False

    self.current_launched = None
    self.status = ''

  def create_ui(self):
    self.widget = QtWidgets.QWidget(self)
    self.setCentralWidget(self.widget)

    # TOP ZONE: les boutons de lancement de son
    self.playbuttonbox = QtWidgets.QGridLayout()
    self.playbutton_widgets = []
    self.create_play_buttons()

    self.topzone = QtWidgets.QHBoxLayout()
    self.topzone.addLayout(self.playbuttonbox)

    # BOTTOM ZONE: la progress bar, les timers, le volume
    self.positionslider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
    self.positionslider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.positionslider.setToolTip("Position")
    self.positionslider.setMaximum(1000)
    self.positionslider.sliderMoved.connect(self.set_position)
    self.positionslider.sliderPressed.connect(self.set_position)

    self.hbuttonbox = QtWidgets.QHBoxLayout()

    self.timelabel = QtWidgets.QLabel()
    self.timelabel.setFont(QtGui.QFont('Arial', 60))
    self.timelabel.setText(self.get_time_info())

    self.globaltimelabel = QtWidgets.QLabel()
    self.globaltimelabel.setFont(QtGui.QFont('Arial', 60))
    self.globaltimelabel.setText(self.get_global_time_info())

    self.volumeslider = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical, self)
    self.volumeslider.setMaximum(100)
    self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
    self.volumeslider.setToolTip("Volume")
    self.volumeslider.valueChanged.connect(self.set_volume)
    
    self.hbuttonbox.addWidget(self.globaltimelabel)
    self.hbuttonbox.addStretch(1)
    self.hbuttonbox.addWidget(self.timelabel)
    self.hbuttonbox.addWidget(self.volumeslider)

    self.bottomzone = QtWidgets.QVBoxLayout()
    self.bottomzone.addWidget(self.positionslider)
    self.bottomzone.addLayout(self.hbuttonbox)

    # GLOBAL LAYOUT
    self.vboxlayout = QtWidgets.QVBoxLayout()
    self.vboxlayout.addLayout(self.topzone)
    self.vboxlayout.addLayout(self.bottomzone)
    self.widget.setLayout(self.vboxlayout)

    menu_bar = self.menuBar()
    # File menu
    file_menu = menu_bar.addMenu("File")
    # Add actions to file menu
    open_file_action = QtGui.QAction("Load conf.json", self)
    close_action = QtGui.QAction("Close App", self)
    file_menu.addAction(open_file_action)
    file_menu.addAction(close_action)

    open_file_action.triggered.connect(self.open_file)
    close_action.triggered.connect(sys.exit)

    self.timer = QtCore.QTimer(self)
    self.timer.setInterval(200)
    self.timer.timeout.connect(self.update_ui)
    self.timer.start()


  def create_play_buttons(self):
    self.remove_play_buttons()
    self.playbutton = {}
    for i, conf_item in enumerate(self.conf):
      shortcut = f'[{self.kbd[i]}] ' if i < 26 else ''
      b = QtWidgets.QPushButton(shortcut + conf_item['label'])
      b.setCheckable(True)
      b.setFont(QtGui.QFont('Arial', 20))
      b.clicked[bool].connect(self.launch)
      self.playbutton_widgets.append(b)
      self.playbuttonbox.addWidget(b, i%NB_ROW_MAX, int(i/NB_ROW_MAX))
      self.playbutton[i] = b


  def remove_play_buttons(self):
    for b in self.playbutton_widgets:
      self.playbuttonbox.removeWidget(b)
    self.playbutton_widgets = []


  def open_file(self):
    dialog_txt = "Choose conf File"
    filename = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('.'))
    # print(filename)
    if not filename:
      return
    # self.conf_dirname = filename[0].rsplit('/',1)[0]
    self.load_conf(filename[0])
    self.create_play_buttons()
        

  def launch(self):
    checked = []
    for i, b in enumerate(self.conf):
      if self.playbutton[i].isChecked():
        self.playbutton[i].setChecked(False)
        checked.append(i)
    if len(checked) == 0:
      self.current_launched = None
    elif len(checked) == 1:
      self.current_launched = checked[0]
    else:
      if checked[0] == self.current_launched:
        self.current_launched = checked[1]
      else:
        self.current_launched = checked[0]
    if self.current_launched is not None:
      self.playbutton[self.current_launched].setChecked(True)
    self.play_sound(self.current_launched)
    self.update_status()


  def update_status(self):
    self.setWindowTitle(self.status)


  def get_filename(self, rank):
    return self.conf[rank]['file']


  def launch_from_keyboard(self, key):
    rank = self.kbd.find(chr(key))
    if rank == -1:
      return
    if rank > len(self.conf):
      return
    # print(self.conf[rank])
    self.playbutton[rank].setChecked(not self.playbutton[rank].isChecked())
    self.launch()


  def keyPressEvent(self, event):
    key = event.key()
    # print('pressed from myDialog: ', key)
    if key == Qt.Key.Key_Escape.value:
        self.close()
    if ord('A') <= key and key <= ord('Z'):
      self.launch_from_keyboard(key)
    if key == Qt.Key.Key_Space.value:
      self.stop_sound()


  def play_sound(self, rank):
    self.timer.stop()
    if rank is not None:
      fullpath = self.conf_dirname + '/' + self.get_filename(rank)
      try:
        with open(fullpath) as dummy:
          pass
      except FileNotFoundError:
        self.status = f'File not found: {fullpath}'
        self.stop_sound()
        self.timer.start()
        return
      self.status = f'Playing: {fullpath}'
      self.media = self.instance.media_new_path(fullpath)
      self.mediaplayer.set_media(self.media)
      self.mediaplayer.play()
      self.is_paused = False
    else:
      self.stop_sound()
    self.timer.start()

  def stop_sound(self):
    # self.timer.stop()
    self.mediaplayer.stop()
    self.status = 'Stopped'
    self.is_paused = True
    self.current_launched = None
    for i in range(len(self.conf)):
      self.playbutton[i].setChecked(False)
    # self.timer.start()

  def set_volume(self, volume):
    self.mediaplayer.audio_set_volume(volume)

  def get_time_info(self):
    if self.mediaplayer.is_playing():
      return f'{self.milliseconds_to_string(self.mediaplayer.get_time())} / {self.milliseconds_to_string(self.media.get_duration())}'
    return 'Stopped'

  def get_global_time_info(self):
    now = datetime.now()
    return now.strftime("%H:%M:%S") 

  def milliseconds_to_string(self, ms):
    m = int(ms / 60000)
    s = int(ms / 1000) % 60
    return f'{m}:{s:02}'

  def update_ui(self):
    self.globaltimelabel.setText(self.get_global_time_info())

    # media_pos = 0
    media_pos = int(self.mediaplayer.get_position() * 1000)
    self.positionslider.setValue(media_pos)
    self.timelabel.setText(self.get_time_info())

    if not self.mediaplayer.is_playing():
      self.timer.stop()
      if not self.is_paused:
        self.stop_sound()
      # self.timer.start()
    self.update_status()


  def load_conf(self, conffile):
    try:
      with open(conffile) as jsonfile:
        stringdata = jsonfile.read()
        self.conf = json.loads(stringdata)
        self.conf_dirname = conffile.rsplit('/',1)[0]
    except:
      self.conf = []
      self.conf_dirname = ''


  def set_position(self, pos=None):
    """Set the movie position according to the position slider.
    """
    # self.timer.stop()
    if pos == None:
        pos = self.positionslider.value()
    # self.mediaplayer.set_position(pos / 1000.0)
    # self.timer.start()


def main():
  # conf = []
  # conf_file = './conf.json'
  # if len(sys.argv) == 2:
  #   conf_file = sys.argv[1]
  # conf = load_conf(conf_file)
  # import code; code.interact(local=locals())
  app = QtWidgets.QApplication(sys.argv)
  launchpad = Launchpad()
  launchpad.show()
  launchpad.resize(800, 600)
  sys.exit(app.exec())


if __name__ == "__main__":
  main()
