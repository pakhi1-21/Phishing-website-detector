import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox
)
from url_prep import url_prep, get_model
import pandas as pd

class PredictionWorker(QThread):
    result_ready = pyqtSignal(str)

    def __init__(self, url_text):
        super().__init__()
        self.url_text = url_text

    def run(self):
        try:
            url, error = url_prep(self.url_text)
            url_df = pd.DataFrame([url])
            
            # Get the model using the get_model function
            model = get_model()
            prediction = model.predict(url_df)

            if prediction[0] == 0:
                result = "Legitimate"
                color = "#00FF00"
            else:
                result = "Phishing"
                color = "#FF0000"

            warning = "<br><span style='color:#FFA500;'>⚠️ Request error occurred. Treat cautiously.</span>" if error else ""
            message = f"<span style='color:{color};'>Prediction: {result}</span>{warning}"

        except Exception as e:
            message = f"<span style='color:red;'>Error: {e}</span>"

        self.result_ready.emit(message)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(1000, 700)
        self.setWindowTitle('Phishing URL Scanner [Fast Mode]')

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(10, 10, 10))
        self.setPalette(palette)

        base_font = QFont("Consolas", 12)
        self.setFont(base_font)

        layout = QVBoxLayout()

        group_box = QGroupBox('Enter URL')
        group_box.setStyleSheet("""
            QGroupBox {
                color: #00FF66;
                font-size: 20px;
                border: 1px solid #00FF66;
                border-radius: 5px;
                margin-top: 20px;
            }
        """)
        group_layout = QVBoxLayout()

        self.lineEdit = QLineEdit()
        self.lineEdit.setFont(QFont("Consolas", 14))
        self.lineEdit.setStyleSheet("""
            QLineEdit {
                background-color: #111;
                color: #0f0;
                border: 1px solid #0f0;
                padding: 10px;
            }
        """)
        group_layout.addWidget(self.lineEdit)
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)

        button_layout = QHBoxLayout()

        self.btn = QPushButton('Scan')
        self.btn.setFixedSize(120, 40)
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #000;
                color: #0f0;
                border: 1px solid #0f0;
            }
            QPushButton:pressed {
                background-color: #0f0;
                color: #000;
            }
        """)
        self.btn.clicked.connect(self.on_click)
        button_layout.addWidget(self.btn)

        self.clear_btn = QPushButton('Clear')
        self.clear_btn.setFixedSize(120, 40)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #000;
                color: #f00;
                border: 1px solid #f00;
            }
            QPushButton:pressed {
                background-color: #f00;
                color: #000;
            }
        """)
        self.clear_btn.clicked.connect(self.on_clear)
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

        self.label = QLabel('Prediction will appear here.')
        self.label.setStyleSheet("color: #00FFFF; font-size: 18px;")
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        layout.addWidget(self.label)

        self.setLayout(layout)

    def on_click(self):
        url_text = self.lineEdit.text().strip()
        if not url_text:
            self.label.setText("<span style='color:yellow;'>Please enter a URL.</span>")
            return

        self.label.setText("<span style='color:cyan;'>Analyzing...</span>")
        self.thread = PredictionWorker(url_text)
        self.thread.result_ready.connect(self.display_result)
        self.thread.start()

    def display_result(self, result):
        self.label.setText(result)

    def on_clear(self):
        self.lineEdit.clear()
        self.label.setText("Prediction will appear here.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())