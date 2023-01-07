pip install nuitka3

`nuitka3 --macos-target-arch=arm64 pad.py`
OK, construite `./pad.bin`


`nuitka3 --macos-target-arch=arm64 --standalone --disable-console --macos-create-app-bundle --macos-app-icon=icon.png pad.py`


pip install py2app
mkdir build
py2applet pad.py
open -a pad.app