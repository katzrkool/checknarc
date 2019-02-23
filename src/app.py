from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QGroupBox, QDesktopWidget, QLineEdit, QPushButton,
                             QProgressBar, QInputDialog, QFileDialog, QCheckBox, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from src.scraper import Scraper
import sys
import json
from pathlib import Path
import webbrowser
import warnings
from time import sleep
warnings.filterwarnings("ignore")

class application(QMainWindow):

    prefs = {}
    login = {}
    defaultValues = {
        "username": "",
        "password": ""
    }

    def __init__(self):
        super().__init__()

        self.mainPage = QGroupBox()

        self.saveLogin = False;

        self.fetchPrefs()

        self.initUI()
        self.mainPage.show()
        self.pop = None

    def fetchPrefs(self):
        try:
            with open("preferences.json") as f:
                self.prefs = json.load(f)
                self.login = self.prefs["login"]
                if len(self.login["username"]) > 0 and len(self.login["password"]) > 0:
                    self.toggleLogin(Qt.Checked)
        except:
            self.login.update(self.defaultValues)

    def initUI(self):

        mainPage = self.mainPage
        self.mainPage.setWindowIcon(QIcon("../img/icon.svg"))
        mainPage.setStyleSheet("QGroupBox {background-image: url(../img/background.png); margin: -5px;}")

        mainPage.usernameLabel = QLabel("Username:", mainPage)
        mainPage.usernameLabel.move(125, 100)

        mainPage.usernameInput = QLineEdit(mainPage)
        mainPage.usernameInput.move(225, 100)
        mainPage.usernameInput.resize(150, 20)
        mainPage.usernameInput.setText(self.login["username"])

        mainPage.passwordLabel = QLabel("Password:", mainPage)
        mainPage.passwordLabel.move(125, 150)

        mainPage.passwordInput = QLineEdit(mainPage)
        mainPage.passwordInput.move(225, 150)
        mainPage.passwordInput.resize(150, 20)
        mainPage.passwordInput.setEchoMode(QLineEdit.Password)
        mainPage.passwordInput.setText(self.login["password"])
        mainPage.passwordInput.returnPressed.connect(self.runScraper)

        mainPage.saveLogin = QCheckBox("Save Login", mainPage)
        if self.saveLogin:
            mainPage.saveLogin.setCheckState(Qt.Unchecked)
        else:
            mainPage.saveLogin.setCheckState(Qt.Checked)
        mainPage.saveLogin.move(400, 150)
        mainPage.saveLogin.toggle()
        mainPage.saveLogin.stateChanged.connect(self.toggleLogin)

        mainPage.submit = QPushButton("Submit", mainPage)
        mainPage.submit.resize(mainPage.submit.sizeHint())
        mainPage.submit.move(200, 200)
        mainPage.submit.clicked.connect(self.runScraper)

        mainPage.cancel = QPushButton("Cancel", mainPage)
        mainPage.cancel.resize(mainPage.submit.sizeHint())
        mainPage.cancel.move(300, 200)

        mainPage.status = QLabel("", mainPage)
        mainPage.status.move(150, 300)
        mainPage.status.resize(300,20)
        mainPage.status.setAlignment(Qt.AlignCenter)

        mainPage.progressBar = QProgressBar(mainPage)
        mainPage.progressBar.move(125, 250)
        mainPage.progressBar.resize(350, 15)

        mainPage.help = QPushButton("Help", mainPage)
        mainPage.help.resize(mainPage.help.sizeHint())
        mainPage.help.move(450, 350)
        mainPage.help.clicked.connect(lambda: webbrowser.open("https://github.com/katzrkool/checknarc#usage"))

        mainPage.setFixedSize(600,400)
        self.center()

        mainPage.setWindowTitle("CheckNarc")

    def toggleLogin(self, state):
        if state == Qt.Checked:
            self.saveLogin = True
        else:
            self.saveLogin = False


    @pyqtSlot(str)
    def setStatus(self, status):
        self.mainPage.status.setText(status)
        if status == "Incorrect Login":
            alert = QMessageBox()
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Incorrect Login!")
            alert.setStandardButtons(QMessageBox.Ok)
            alert.exec_()
            self.mainPage.passwordInput.setText("")

    @pyqtSlot(int)
    def updateProgress(self, value):
        self.mainPage.progressBar.setValue(value)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)

        self.move(qr.topLeft())


    def runScraper(self,):

        username = self.mainPage.usernameInput.text()
        password = self.mainPage.passwordInput.text()

        if len(username) + len(password) == 0:
            self.setStatus("Please enter a username and password!")
            alert = QMessageBox()
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Please enter a username and password!")
            alert.setStandardButtons(QMessageBox.Ok)
            alert.exec_()
            return False
        elif len(username) == 0:
            self.setStatus("Please enter a username!")
            alert = QMessageBox()
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Please enter a username!")
            alert.setStandardButtons(QMessageBox.Ok)
            alert.exec_()
            return False
        elif len(password) == 0:
            self.setStatus("Please enter a password!")
            alert = QMessageBox()
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Please enter a password!")
            alert.setStandardButtons(QMessageBox.Ok)
            alert.exec_()
            return False

        data = {}

        overwrite = False
        if self.saveLogin:
            try:
                with open("preferences.json") as f:
                    login = json.load(f)["login"]
                    if login["username"] != username or login["password"] != password:
                        overwrite = True
            except:
                overwrite = True
            finally:
                if overwrite == True:
                    data.update({"login":{"username": username, "password": password}})
                    with open("preferences.json", "w") as fp:
                        json.dump(data, fp)

        self.setStatus("Pick a file to read from")
        pickFile = QMessageBox()
        pickFile.setIcon(QMessageBox.Question)
        pickFile.setText("Please pick a csv file to get patient names from.")
        pickFile.setStandardButtons(QMessageBox.Ok)
        pickFile.exec_()

        fname = QFileDialog.getOpenFileName(self, 'Open file', str(Path.home()), "CSV (*.csv)")
        if len(fname[0]) > 0:
            self.csvFile = fname[0]
        else:
            self.setStatus("Cancelled")
            return False

        self.setStatus("Pick a folder to save in.")
        pickFolder = QMessageBox()
        pickFolder.setIcon(QMessageBox.Question)
        pickFolder.setText("Please pick a folder to save data in.")
        pickFolder.setStandardButtons(QMessageBox.Ok)
        pickFolder.exec_()

        saveLoc = QFileDialog.getExistingDirectory(self, 'Save Location', str(Path.home()))
        self.saveLoc = saveLoc
        if len(saveLoc[0]) > 0:
            self.csvFile = fname[0]
        else:
            self.setStatus("Cancelled")
            return False

        self.sr = scrapeRemote(self.csvFile, username, password, self.saveLoc)

        self.mainPage.progressBar.setValue(0)

        self.sr.status.connect(self.setStatus)
        self.sr.progress.connect(self.updateProgress)
        self.sr.supervisorList.connect(self.asker)
        self.mainPage.cancel.clicked.connect(self.sr.stop)

        self.sr.start()

    @pyqtSlot(list)
    def asker(self, supervisorList):
            self.setStatus("Please select a Supervisor")
            asker = QInputDialog.getItem(self, "Supervisor Selection", "Pick a Supervisor to search under", [i['name'] for i in supervisorList], 0, False)
            if asker[1] == True:
                self.sr.setSupervisor([x for i, x in enumerate(supervisorList) if x['name'] == asker[0]][0])
                self.setStatus("Preparing to Download")
            else:
                self.setStatus("Cancelling")
                self.sr.stop()
                self.setStatus("Cancelled")

class scrapeRemote(QThread):
    progress = pyqtSignal(int, name="Updated Progress")
    status = pyqtSignal(str, name="Status")
    supervisorList = pyqtSignal(list, name="Supervisor Choices")

    def __init__(self, csvFile: str, username: str, password: str, saveLoc: str, parent=None):
        super(scrapeRemote, self).__init__(parent)
        self.username = username
        self.password = password
        self.csvFile = csvFile
        self.saveLoc = saveLoc
        self._isRunning = True
        self.supervisor = 'unset'

    def run(self):
        self.status.emit("Initializing")
        scraper = Scraper(self.csvFile, self.saveLoc)
        initState = scraper.initSession(self.username, self.password)
        if initState[0] == False:
            self.status.emit(initState[1])
            self._isRunning = False
            return

        supervisors = scraper.detectSupervisor()
        if len(supervisors) > 0:
            self.supervisorList.emit(supervisors)
        else:
            self.supervisor = None

        while self.supervisor == 'unset':
            sleep(0.1)

        if self._isRunning:
            scraper.setSupervisor(self.supervisor)
            data = []
            for iteration, i in enumerate(scraper.patients):
                QCoreApplication.processEvents()
                if self._isRunning:
                    patient = scraper.patientLookup(i['first'], i['last'], i['dob'])
                    self.status.emit(f'Downloaded {patient["Last Name"]}')
                    self.progress.emit(int(((iteration + 1) * 100) / len(scraper.patients) + 1))
                    data.append(patient)
            if self._isRunning:
                self.status.emit('Downloading PDF reports')
                scraper.pdfFetch(scraper.pdfLinks)
                self.progress.emit(int((len(scraper.patients) / len(scraper.patients) + 1)))
            if self._isRunning:
                self.status.emit('Exporting Data')
                scraper.csvExport(data)
                self.progress.emit(100)
                self.status.emit("Finished!")


    def setSupervisor(self, supervisor):
        self.supervisor = supervisor

    def stop(self):
        self._isRunning = False
        self.status.emit("Cancelling")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ct = application()
    sys.exit(app.exec_())
