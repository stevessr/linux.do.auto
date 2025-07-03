import sys
import subprocess
import os
import glob
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QTextEdit, QCheckBox, QTabWidget, QLabel, QMessageBox, QComboBox, QLineEdit, QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# --- CONFIGURATION ---
READ_SCRIPT_PATH = "E:/linux.do.auto/read_linuxdo.py"
LOGIN_SCRIPT_PATH = "E:/linux.do.auto/login_linuxdo.py"
SCRIPT_DIR = "E:/linux.do.auto/"
# --- END CONFIGURATION ---

class Worker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, script_path, args=None):
        super().__init__()
        self.script_path = script_path
        self.args = args if args is not None else []

    def run(self):
        command = ["uv", "run", self.script_path] + self.args

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            for line in iter(process.stdout.readline, ''):
                self.output_signal.emit(line)
            for line in iter(process.stderr.readline, ''):
                self.output_signal.emit(line)

            process.wait()
        except Exception as e:
            self.output_signal.emit(f"Error executing script: {e}\n")
        finally:
            self.finished_signal.emit()

class LinuxDoReaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.read_worker = None
        self.login_worker = None

    def initUI(self):
        self.setWindowTitle('Linux.do Reader UI')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # --- Script Execution Tab ---
        self.script_tab = QWidget()
        self.script_layout = QVBoxLayout()

        # Controls layout
        controls_layout = QHBoxLayout()
        self.run_button = QPushButton('Run Read Script')
        self.run_button.clicked.connect(self.run_read_script)
        controls_layout.addWidget(self.run_button)

        self.force_stop_button = QPushButton('Force Stop')
        self.force_stop_button.clicked.connect(self.force_stop_script)
        self.force_stop_button.setEnabled(False) # Initially disabled
        controls_layout.addWidget(self.force_stop_button)

        self.headful_checkbox = QCheckBox('Headful Mode')
        controls_layout.addWidget(self.headful_checkbox)
        controls_layout.addStretch(1) # Pushes widgets to the left

        self.script_layout.addLayout(controls_layout)

        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.script_layout.addWidget(self.output_text)

        self.script_tab.setLayout(self.script_layout)
        self.tabs.addTab(self.script_tab, "Script Execution")

        # --- Cookie Management Tab ---
        self.cookie_tab = QWidget()
        self.cookie_layout = QVBoxLayout()

        # Cookie file selection
        cookie_select_layout = QHBoxLayout()
        cookie_select_layout.addWidget(QLabel("Select Cookie File:"))
        self.cookie_file_combo = QComboBox()
        self.cookie_file_combo.currentIndexChanged.connect(self.load_cookies_display)
        cookie_select_layout.addWidget(self.cookie_file_combo)

        self.refresh_cookie_button = QPushButton("Refresh List")
        self.refresh_cookie_button.clicked.connect(self.populate_cookie_files_dropdown)
        cookie_select_layout.addWidget(self.refresh_cookie_button)
        cookie_select_layout.addStretch(1)
        self.cookie_layout.addLayout(cookie_select_layout)

        cookie_controls_layout = QHBoxLayout()
        self.load_cookie_button = QPushButton('Load Selected Cookie')
        self.load_cookie_button.clicked.connect(self.load_cookies_display)
        cookie_controls_layout.addWidget(self.load_cookie_button)

        self.delete_cookie_button = QPushButton('Delete Selected Cookie')
        self.delete_cookie_button.clicked.connect(self.delete_cookies_file)
        cookie_controls_layout.addWidget(self.delete_cookie_button)

        self.run_login_button = QPushButton('Run Login Script (New/Existing)')
        self.run_login_button.clicked.connect(self.prompt_and_run_login_script)
        cookie_controls_layout.addWidget(self.run_login_button)
        cookie_controls_layout.addStretch(1)

        self.cookie_layout.addLayout(cookie_controls_layout)

        self.cookie_content_label = QLabel("Content of selected cookie file:")
        self.cookie_layout.addWidget(self.cookie_content_label)

        self.cookie_content_text = QTextEdit()
        self.cookie_content_text.setReadOnly(True)
        self.cookie_layout.addWidget(self.cookie_content_text)

        self.cookie_tab.setLayout(self.cookie_layout)
        self.tabs.addTab(self.cookie_tab, "Cookie Management")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        # Initial population of cookie files
        self.populate_cookie_files_dropdown()

    def populate_cookie_files_dropdown(self):
        self.cookie_file_combo.clear()
        json_files = glob.glob(os.path.join(SCRIPT_DIR, "*.json"))
        # Filter out read_topics.json if it exists
        json_files = [f for f in json_files if os.path.basename(f) != "read_topics.json"]
        
        if not json_files:
            self.cookie_file_combo.addItem("No cookie files found")
            self.set_cookie_buttons_enabled(False)
            self.cookie_content_text.setText("No cookie file selected or file not found.") # Clear content
            self.output_text.append("No cookie file selected or file not found.") # Clear output
        else:
            for f in json_files:
                self.cookie_file_combo.addItem(os.path.basename(f))
            self.set_cookie_buttons_enabled(True)
            self.load_cookies_display() # Only load content if there are actual files

    def get_selected_cookie_file(self):
        selected_file = self.cookie_file_combo.currentText()
        if selected_file == "No cookie files found":
            return None
        return os.path.join(SCRIPT_DIR, selected_file)

    def run_read_script(self):
        selected_cookie_file = self.get_selected_cookie_file()
        if not selected_cookie_file or not os.path.exists(selected_cookie_file):
            QMessageBox.warning(self, "Error", "Please select a valid cookie file first.")
            return

        self.output_text.clear()
        self.output_text.append("Starting read script...")
        self.set_all_buttons_enabled(False)

        args = []
        if self.headful_checkbox.isChecked():
            args.append("--headful")
        args.extend(["--cookie-file", selected_cookie_file])

        self.read_worker = Worker(READ_SCRIPT_PATH, args)
        self.read_worker.output_signal.connect(self.append_output)
        self.read_worker.finished_signal.connect(self.script_finished)
        self.read_worker.start()

    def prompt_and_run_login_script(self):
        text, ok = QInputDialog.getText(self, 'New/Existing Cookie File', 
                                         'Enter filename for cookies (e.g., my_account.json):',
                                         QLineEdit.Normal, "cookies.json")
        if ok and text:
            login_cookie_file = os.path.join(SCRIPT_DIR, text)
            self.run_login_script(login_cookie_file)

    def run_login_script(self, cookie_filename):
        self.output_text.clear()
        self.output_text.append(f"Starting login script for {os.path.basename(cookie_filename)}... Please follow instructions in the browser if it opens.\n")
        self.set_all_buttons_enabled(False)

        # Login script always runs headful for user interaction
        args = ["--cookie-file", cookie_filename]
        self.login_worker = Worker(LOGIN_SCRIPT_PATH, args)
        self.login_worker.output_signal.connect(self.append_output)
        self.login_worker.finished_signal.connect(self.login_script_finished)
        self.login_worker.start()

    def append_output(self, text):
        self.output_text.append(text.strip()) # .strip() to remove extra newlines

    def script_finished(self):
        self.output_text.append("\nRead script finished.")
        self.set_all_buttons_enabled(True)
        self.populate_cookie_files_dropdown() # Refresh cookie display after script finishes

    def login_script_finished(self):
        self.output_text.append("\nLogin script finished. Please check cookies.json.\n")
        self.set_all_buttons_enabled(True)
        self.populate_cookie_files_dropdown() # Refresh cookie display after login script finishes

    def force_stop_script(self):
        if self.read_worker and self.read_worker.isRunning():
            self.read_worker.terminate()
            self.read_worker.wait() # Wait for the thread to actually terminate
            self.output_text.append("\nRead script forcibly stopped.")
        elif self.login_worker and self.login_worker.isRunning():
            self.login_worker.terminate()
            self.login_worker.wait() # Wait for the thread to actually terminate
            self.output_text.append("\nLogin script forcibly stopped.")
        else:
            self.output_text.append("\nNo script is currently running.")
        self.set_all_buttons_enabled(True) # Re-enable all buttons after stopping

    def set_all_buttons_enabled(self, enabled):
        self.run_button.setEnabled(enabled)
        self.load_cookie_button.setEnabled(enabled)
        self.delete_cookie_button.setEnabled(enabled)
        self.run_login_button.setEnabled(enabled)
        self.refresh_cookie_button.setEnabled(enabled)
        self.cookie_file_combo.setEnabled(enabled)
        self.force_stop_button.setEnabled(not enabled) # Force stop is enabled when other buttons are disabled (script running)

    def set_cookie_buttons_enabled(self, enabled):
        self.load_cookie_button.setEnabled(enabled)
        self.delete_cookie_button.setEnabled(enabled)
        self.run_button.setEnabled(enabled) # Also disable run read script if no cookie file

    def load_cookies_display(self):
        selected_cookie_file = self.get_selected_cookie_file()
        self.cookie_content_text.clear()
        if selected_cookie_file and os.path.isfile(selected_cookie_file):
            try:
                with open(selected_cookie_file, 'r') as f:
                    content = f.read()
                    self.cookie_content_text.setText(content)
                self.output_text.append(f"Loaded content of {os.path.basename(selected_cookie_file)}")
            except Exception as e:
                self.cookie_content_text.setText(f"Error reading file: {e}")
                self.output_text.append(f"Error reading {os.path.basename(selected_cookie_file)}: {e}")
        else:
            self.cookie_content_text.setText("No cookie file selected or file not found.")
            # self.output_text.append("No cookie file selected or file not found.") # This line is redundant and can be removed

    def delete_cookies_file(self):
        selected_cookie_file = self.get_selected_cookie_file()
        if not selected_cookie_file:
            QMessageBox.warning(self, "Error", "No cookie file selected to delete.")
            return

        if os.path.exists(selected_cookie_file):
            reply = QMessageBox.question(self, 'Confirm Delete', 
                                         f"Are you sure you want to delete {os.path.basename(selected_cookie_file)}?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    os.remove(selected_cookie_file)
                    self.output_text.append(f"Successfully deleted {os.path.basename(selected_cookie_file)}")
                    self.populate_cookie_files_dropdown() # Refresh display
                except Exception as e:
                    self.output_text.append(f"Error deleting {os.path.basename(selected_cookie_file)}: {e}")
        else:
            self.output_text.append(f"{os.path.basename(selected_cookie_file)} does not exist. Nothing to delete.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LinuxDoReaderApp()
    ex.show()
    sys.exit(app.exec_())