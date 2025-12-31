#!/usr/bin/env python3

import sys, json, httpx, threading
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit
)

BASE_URL = "http://172.20.10.3:8000"

class StreamThread(QThread):
    new_line = Signal(str)              
    orangedef run(self):
        while True:
            try:
                with httpx.stream("GET", f"{BASE_URL}/stream", timeout=None) as r:
                    for chunk in r.iter_text():
                        if chunk.startswith("data:"):
                            obj = json.loads(chunk[5:].strip())
                            cm = obj["cm"]
                            line = f"[sensor] {cm:.1f} cm"
                            self.new_line.emit(line)
            except Exception as e:
                self.new_line.emit(f"[stream error] {e}")
                QThread.msleep(2000)    # retry after 2 s

class PiWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pi Ultrasonic 1/0  +  Console")
        self.resize(400, 300)

        # ---- widgets ----
        self.label = QLabel("–", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size:30px;")
        self.btn_on  = QPushButton("Enable")
        self.btn_off = QPushButton("Disable")
        self.console = QTextEdit(readOnly=True)
        self.show_btn = QPushButton("Show console")

        # ---- layout ----
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.label)
        hbox = QHBoxLayout()
        hbox.addWidget(self.btn_on)
        hbox.addWidget(self.btn_off)
        hbox.addWidget(self.show_btn)
        vbox.addLayout(hbox)
        vbox.addWidget(self.console)

        # ---- behaviour ----
        self.btn_on.clicked.connect(lambda: self.set_enabled(True))
        self.btn_off.clicked.connect(lambda: self.set_enabled(False))
        self.show_btn.clicked.connect(self.start_stream)

        # ---- polling 1/0 ----
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_distance)
        self.timer.start(500)

        self.poll_distance()

    # ---------- HTTP ----------
    def set_enabled(self, state):
        try:
            httpx.post(f"{BASE_URL}/button", json={"state": int(state)}, timeout=2)
            self.poll_distance()
        except Exception as e:
            self.console.append(f"[button error] {e}")

    def poll_distance(self):
        try:
            val = httpx.get(f"{BASE_URL}/distance", timeout=2).text.strip()
            self.label.setText(val)
            self.label.setStyleSheet("font-size:30px; color:green;" if val == "1" else "color:red;")
        except Exception as e:
            self.label.setText("0")
            self.console.append(f"[poll error] {e}")

    # ---------- streaming console ----------
    def start_stream(self):
        if not hasattr(self, '_stream_thread'):
            self._stream_thread = StreamThread()
            self._stream_thread.new_line.connect(self.console.append)
            self._stream_thread.start()
        self.console.append("[console] streaming started ...")

# ---------------- run ----------------
if __name__ == "__main__":
    from PySide6.QtCore import QTimer   # re-import avoids linter warning
    app = QApplication(sys.argv)
    win = PiWindow()
    win.show()
    sys.exit(app.exec())