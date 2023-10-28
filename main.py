import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QComboBox, QVBoxLayout, QWidget, QProgressBar, QSizePolicy
from PyQt5.QtCore import QThread, pyqtSignal
import requests
from portablemc.standard import Version, Context, Watcher
from portablemc.auth import OfflineAuthSession
import time
import uuid
import json
import os

class JAML(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JAML")
        self.setGeometry(100, 100, 400, 250)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.main_label = QLabel("Just Another Minecraft Launcher")
        self.version_label = QLabel("Select Version:")
        self.version_label.setStyleSheet("font-size: 16px;")
        self.main_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.main_label)
        self.layout.addWidget(self.version_label)

        self.version_combobox = QComboBox()
        self.layout.addWidget(self.version_combobox)

        self.username_label = QLabel("Minecraft Username:")
        self.username_edit = QLineEdit()
        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_edit)

        self.launch_button = QPushButton("Launch Minecraft")
        self.launch_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")
        self.layout.addWidget(self.launch_button)
        self.launch_button.clicked.connect(self.launch_minecraft)

        self.progress_bar = QProgressBar()
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.progress_bar)

        self.main_label = QLabel()
        self.layout.addWidget(self.main_label)

        # Add a QLabel for the hyperlink
        self.link_label = QLabel()
        self.link_label.setText('<a href="https://github.com/csoftware-arigpt/JAML">GitHub Repository</a>')
        self.link_label.setOpenExternalLinks(True)
        self.layout.addWidget(self.link_label)

        self.central_widget.setLayout(self.layout)

        self.load_minecraft_versions()
        self.load_saved_data()

    def load_minecraft_versions(self):
        try:
            version_requests = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json").json()
            version_list = [version['id'] for version in version_requests['versions']]
            self.version_combobox.addItems(version_list)
        except Exception as e:
            self.main_label.setText("Failed to load Minecraft versions.")
            logging.error(f"Failed to load Minecraft versions: {str(e)}")

    def load_saved_data(self):
        if os.path.isfile('user_data.json'):
            with open('user_data.json', 'r') as json_file:
                data = json.load(json_file)
                username = data.get('username')
                uuid = data.get('uuid')
                if username:
                    self.username_edit.setText(username)
                if uuid:
                    self.uuid = uuid

    def launch_minecraft(self):
        selected_version = self.version_combobox.currentText()
        version = Version(selected_version, context=Context())

        username = self.username_edit.text()
        if hasattr(self, 'uuid'):
            auth_session = OfflineAuthSession(username, self.uuid)
        else:
            auth_session = OfflineAuthSession(username, self.generate_uuid())
        version.auth_session = auth_session

        self.worker = MinecraftWorker(version)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.start()

        user_data = {
            'username': username,
            'uuid': auth_session.uuid,
        }
        with open('user_data.json', 'w') as json_file:
            json.dump(user_data, json_file)

    def generate_uuid(self):
        return str(uuid.uuid4())

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if value == 25:
            self.main_label.setText("Downloading Minecraft")
        elif value == 50:
            self.main_label.setText("Launching Minecraft")
        elif value == 100:
            self.main_label.setText("Minecraft stopped")
        elif value == 32:
            self.main_label.setText("Error detected. Check logs for more info")
            logging.error("Error detected. Check logs for more info")

class MinecraftWorker(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self, version):
        super().__init__()
        self.version = version

    def run(self):
        try:
            self.progress_signal.emit(25)
            env = self.version.install()
            self.progress_signal.emit(50)
            env.run()
            self.progress_signal.emit(100)
            time.sleep(1)
            self.progress_signal.emit(0)
        except Exception as e:
            self.progress_signal.emit(32)
            logging.error(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    launcher = JAML()
    launcher.show()
    sys.exit(app.exec_())

