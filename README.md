# Gesture Shooter

Aim at the target and score as many hits as you can in 30 seconds. You start with five health points and lose one for each miss.

## Install and play

Use Python 3.12 and run these commands from the repository root.

### macOS and Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The game starts in mouse mode. Aim with the mouse and left-click to shoot. With a fresh checkout, the game draws its own background, target, and crosshair and plays silently. To customize it, place `bg.jpg`, `enemy.png`, `crosshair.png`, or `shoot.wav` in `assets/`.

## Optional webcam controls

To enable gesture mode on a machine with a webcam, install the optional libraries into the same Python 3.12 virtual environment. On Windows, replace `.venv/bin/python` with `.\.venv\Scripts\python.exe`.

```bash
.venv/bin/python -m pip install "mediapipe==0.10.21" "opencv-contrib-python==4.11.0.86" "numpy==1.26.4"
```

Launch the game and press `G` to switch to gesture mode. Move your index finger to aim and pinch it against your thumb to shoot. Press `G` again to return to mouse mode. If the libraries or webcam are unavailable, the game stays in mouse mode and prints the reason in the terminal.
