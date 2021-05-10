# TO-DO
# 3) Frontend of the main window
# 6) Check if news have correct encoding
import os
import sys
import json
import time
import requests
import subprocess
from lxml import etree
from bs4 import BeautifulSoup
from lxml import html

from PIL import Image
import PIL.ImageQt as PQ

import PyQt5
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeySequence, QPalette, QColor, QPixmap, QIcon
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtGui, QtCore

from forex_python.converter import CurrencyRates

from geopy.geocoders import Nominatim
import pyowm
from pyowm import OWM
from pyowm.utils.config import get_default_config

TEMP_FOLDER = "C:\\Users\\{}\\Documents\\NewsWeatherSysTrayPy".format(os.getlogin())
TEMP_FILE = "C:\\Users\\{}\\Documents\\NewsWeatherSysTrayPy\\NewsWeatherSysTrayPy.json".format(os.getlogin())
DATA_FILE = "C:\\Users\\{}\\Documents\\NewsWeatherSysTrayPy\\data.json".format(os.getlogin())
ICON_IMAGE = None

data = {
    'time': None
}
data['currency'] = {
    'error': None,
    'EUR2RUB': None,
    'USD2RUB': None
}
data['weather'] = {
    'api_key': None, 
    'error': None,
    'lat': None, 
    'lon': None,
    'city': None,
    'status': None,
    'icon': None,
    'temperature': None,
    'humidity': None,
    'pressure': None,
    'wind_speed': None
}
data['main_news'] = {
    'news': [],
    'error': None
}
data['news'] = {
    'news': [],
    'error': None
}
userData = {
    "openweathermap": "API",
    "lat": None,
    "lon": None
}

geolocator = Nominatim(user_agent="NewsWeatherSysTrayPy")

def SaveTempData():
    global userData, data
    with open(TEMP_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def GetTempData(force=False):
    global ICON_IMAGE, userData, data
    if os.path.exists(TEMP_FILE) and not(force):
        with open(TEMP_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)

        if time.time() - data['time'] > 600 or data['weather']['lat'] != userData['lat'] or data['weather']['error'] is not None:
            data['weather']['lat'] = userData['lat']
            data['weather']['lon'] = userData['lon']
            data['weather']['api_key'] = userData['openweathermap']
            data['time'] = time.time()

            GetCurrency()
            GetMainNews()
            GetWeather()
            SaveTempData()    
    else:
        data['time'] = time.time()

        GetCurrency()
        GetMainNews()
        GetWeather()
        SaveTempData()

    try:
        ICON_IMAGE = Image.open(requests.get(data['weather']['icon'], stream=True).raw)
    except requests.exceptions.RequestException as e:
        ICON_IMAGE = None

def GetWeather():
    global userData, data
    config_dict = get_default_config()
    
    config_dict['language'] = 'ru'
    
    owm = OWM(data['weather']['api_key'], config_dict)
    
    mgr = owm.weather_manager()
    try: 
        observation = mgr.weather_at_coords(data['weather']['lat'], data['weather']['lon'])
    except AssertionError:
        data['weather']['error'] = "Invalid lat/lon values"
    except pyowm.commons.exceptions.InvalidSSLCertificateError as e:
        data['weather']['error'] = "No internet connection"
    else:
        w = observation.weather

        data['weather']['status'] = w.detailed_status.capitalize()
        data['weather']['temperature'] = str(w.temperature('celsius')['temp']) + "°C"
        data['weather']['humidity'] = str(w.humidity) + "%"
        data['weather']['pressure'] = str(w.pressure['press']) + " гПa"
        data['weather']['wind_speed'] = str(w.wind()['speed']) + " м/с"
        data['weather']['icon'] = w.weather_icon_url(size='2x')

        location = geolocator.reverse(str(data['weather']['lat']) + "," + str(data['weather']['lon']))
        data['weather']['city'] = location.raw['address'].get('city', "None")

        data['weather']['error'] = None

def GetCurrency():
    global userData, data
    c = CurrencyRates()
    try:
        data['currency']['EUR2RUB'] = round(c.get_rate('EUR', 'RUB'), 2)
        data['currency']['USD2RUB'] = round(c.get_rate('USD', 'RUB'), 2)
    except requests.exceptions.RequestException as e:
        data['currency']['error'] = "No internet connection"
    else:
        data['currency']['error'] = None


def GetMainNews():
    global userData, data
    DATAURL = 'https://yandex.ru/'

    try:
        r = requests.get(DATAURL).text
    except requests.exceptions.RequestException as e:
        data['main_news']['error'] = "No internet connection"
    else:
        soup = BeautifulSoup(r, features="lxml")
        page_list = soup.find('ol', class_='list news__list')

        if len(page_list) == 0:
            data['main_news']['error'] = "Could not find main news: change parser"
        else:
            for i in page_list:
                a = i.find('a')
                try:
                    data['main_news']['news'].append({'label': a['aria-label'], 'url': a['href']})
                except:
                    data['main_news']['error'] = "Error while parsing: change parser"
                    break
                else:
                    data['main_news']['error'] = None

def AskForData():
    global userData, data

    subprocess.check_output('start /wait ' + DATA_FILE, shell=True)

    with open(DATA_FILE, 'r') as f:
        userData = json.load(f)
    
    data['weather']['lat'] = userData['lat']
    data['weather']['lon'] = userData['lon']
    data['weather']['api_key'] = userData['openweathermap']
    GetTempData(True)

class MainWindow(QWidget):
    def __init__(self, coords):
        global userData, data

        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Another Window")
        layout.addWidget(self.label)

        self.setLayout(layout)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.Popup)

        self.setGeometry(coords[0] - 50, coords[1] - 150, 100, 150)
       
        GetTempData()


# class Settings(QWidget):
#     def __init__(self, coords):
#         super().__init__()
#         layout = QVBoxLayout()
#         self.label = QLabel("Settings")
#         layout.addWidget(self.label)

#         self.setLayout(layout)

#         self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
#         self.setWindowFlags(QtCore.Qt.Popup)

#         self.setGeometry(coords[0] - 50, coords[1] - 150, 100, 150)


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        self.w = None
        self.settings = None

        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)

        menu = QtWidgets.QMenu(parent)
        updateAction = menu.addAction("Update")
        settingAction = menu.addAction("Settings")
        exitAction = menu.addAction("Exit")
        self.setContextMenu(menu)

        updateAction.triggered.connect(self.UpdateIcon)
        settingAction.triggered.connect(self.ShowSettings)
        exitAction.triggered.connect(self.Destructor)

        self.UpdateIcon()
        self.activated.connect(self.ShowNewWindow)

    def ShowSettings(self):
        AskForData()

    def Destructor(self, reason):
        QtWidgets.qApp.quit()

    def ShowNewWindow(self, reason):
        if reason == self.Trigger:
            currCoords = self.geometry().getRect()
            if self.w is None:
                self.w = MainWindow(currCoords)
            else:
                self.w.setGeometry(
                    currCoords[0] - 50, currCoords[1] - 150, 100, 150)
            self.w.show()

    def UpdateIcon(self):
        global ICON_IMAGE
        try:
            timer = QtCore.QTimer()
            timer.timeout.connect(self.UpdateIcon)
            timer.start(600000)
            
            if ICON_IMAGE is None:
                icone = "resources/icons/icon.ico"
            else:
                image = PQ.ImageQt(ICON_IMAGE)
                pixmap = QPixmap.fromImage(image)
                icone = QIcon(pixmap)
            
            self.setIcon(QtGui.QIcon(icone))

            GetTempData()
        finally:
            QtCore.QTimer.singleShot(600000, self.UpdateIcon)


def DarkTheme():
    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)

    return palette


if not(os.path.exists(TEMP_FOLDER)):
    os.mkdir(TEMP_FOLDER)

if not(os.path.exists(DATA_FILE)):
    with open(DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(userData, f, indent=4, ensure_ascii=False)
    AskForData()

with open(DATA_FILE, "r", encoding='utf-8') as f:
    userData = json.load(f)

data['weather']['api_key'] = userData['openweathermap']
data['weather']['lat'] = userData['lat']
data['weather']['lon'] = userData['lon']

GetTempData()


appIcon = QtWidgets.QApplication(sys.argv)
appIcon.setStyle("Fusion")
if userData["theme"] == "dark":
    appIcon.setPalette(DarkTheme())
wIcon = QtWidgets.QWidget()
trayIcon = SystemTrayIcon(QtGui.QIcon("resources/icons/icon.ico"), wIcon)
trayIcon.show()

sys.exit(appIcon.exec_())
