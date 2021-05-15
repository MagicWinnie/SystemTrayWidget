# TO-DO
# 1) Add more exception handling
# 2) Add more news
# 3) Use new data when opening widget
# 4) Improve design
# 5) Add scrolling
# 6) Add hyperlinks 
import os
import sys
import json
import time
import requests
import subprocess
from threading import Thread

from lxml import etree
from bs4 import BeautifulSoup
from lxml import html

from PIL import Image
import PIL.ImageQt as PQ

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
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
    "lon": None,
    "theme": "dark",
    "data_update_timeout (sec)": 600,
    "icon_update_timeout (msec)": 1000,
}

HEIGHT = 640
WIDTH = 840

geolocator = Nominatim(user_agent="NewsWeatherSysTrayPy")   

def SaveTempData():
    global userData, data
    with open(TEMP_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def GetTempData():
    global ICON_IMAGE, userData, data

    with open(TEMP_FILE, "r", encoding='utf-8') as f:
        data = json.load(f)
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        userData = json.load(f)

    data['weather']['lat'] = userData['lat']
    data['weather']['lon'] = userData['lon']
    data['weather']['api_key'] = userData['openweathermap']

    GetCurrency()
    GetMainNews()
    GetWeather()
    SaveTempData()    

    try:
        ICON_IMAGE = Image.open(requests.get(data['weather']['icon'], stream=True).raw)
    except requests.exceptions.RequestException as e:
        ICON_IMAGE = None

    data['time'] = time.time()

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
            data['main_news']['news'] = []
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
    GetTempData()

class Updater:
    def __init__(self):
        global data, userData

        self.stopped = False
        self.PreviousTime = None

    def FullUpdate(self):
        if not(os.path.exists(TEMP_FOLDER)):
            os.mkdir(TEMP_FOLDER)

        if not(os.path.exists(DATA_FILE)):
            with open(DATA_FILE, "w", encoding='utf-8') as f:
                json.dump(userData, f, indent=4, ensure_ascii=False)
            AskForData()
        else:
            GetTempData()

    def process(self):
        global ICON_IMAGE
        try:
            while not(self.stopped):
                if self.PreviousTime == -1:
                    GetTempData()
                    self.PreviousTime = time.time()
                elif self.PreviousTime is None:
                    self.FullUpdate()
                    self.PreviousTime = time.time()
                elif time.time() - self.PreviousTime >= userData.get("data_update_timeout", 30):
                    GetTempData()
                    self.PreviousTime = time.time()
        except KeyboardInterrupt:
            self.stopped = True

    def start(self):
        Thread(target=self.process, args=()).start()
        return self

    def stop(self):
        self.stopped = True

up = Updater().start()

class MainWindow(QWidget):
    def __init__(self, coords):
        global userData, data

        super().__init__()
        layout = QGridLayout()

        ##################################### Weather
        WeatherLayout = QGroupBox("Погода")
        layout.addWidget(WeatherLayout, 0, 0)

        WeatherInsideLayout = QVBoxLayout()
        WeatherLayout.setLayout(WeatherInsideLayout)

        # CITY
        if data["weather"]["city"] == None:
            WeatherCity = QLabel("Error")
        else:
            WeatherCity = QLabel(data["weather"]["city"])
        WeatherCity.setFont(QFont('Arial', 14))
        WeatherInsideLayout.addWidget(WeatherCity)

        # IMAGE - INFO
        WeatherInsideLayoutGrid = QGridLayout()
        WeatherInsideLayout.addLayout(WeatherInsideLayoutGrid)

        # INFO
        if data["weather"]["error"] is not None:
            WeatherStatus = QLabel("Error")
            WeatherTemperature = QLabel("Error")
            WeatherHumidity = QLabel("Error")
            WeatherPressure = QLabel("Error")
            WeatherWindSpeed = QLabel("Error")
        else:
            WeatherStatus = QLabel(data['weather']['status'])
            WeatherTemperature = QLabel(data['weather']['temperature'])
            WeatherHumidity = QLabel(data['weather']['humidity'])
            WeatherPressure = QLabel(data['weather']['pressure'])
            WeatherWindSpeed = QLabel(data['weather']['wind_speed'])

        WeatherStatus.setFont(QFont('Arial', 12))
        WeatherTemperature.setFont(QFont('Arial', 12))
        WeatherHumidity.setFont(QFont('Arial', 12))
        WeatherPressure.setFont(QFont('Arial', 12))
        WeatherWindSpeed.setFont(QFont('Arial', 12))

        WeatherInsideLayoutGrid.addWidget(WeatherStatus, 0, 1)
        WeatherInsideLayoutGrid.addWidget(WeatherHumidity, 1, 1)
        WeatherInsideLayoutGrid.addWidget(WeatherPressure, 2, 1)
        WeatherInsideLayoutGrid.addWidget(WeatherWindSpeed, 3, 1)

        WeatherStatus.setAlignment(Qt.AlignRight)
        WeatherHumidity.setAlignment(Qt.AlignRight)
        WeatherPressure.setAlignment(Qt.AlignRight)
        WeatherWindSpeed.setAlignment(Qt.AlignRight)

        # ICON
        WeatherIconLayoutGrid = QGridLayout()
        
        IMAGE = QLabel()
        
        if ICON_IMAGE is None:
            image = "resources/icons/icon.ico"
            pixmap = QtGui.QPixmap(image)
        else:
            image = PQ.ImageQt(ICON_IMAGE)
            pixmap = QPixmap.fromImage(image)

        IMAGE.resize(150, 150)
        IMAGE.setPixmap(pixmap.scaled(IMAGE.size(), Qt.KeepAspectRatio))
        WeatherIconLayoutGrid.addWidget(IMAGE, 0, 0)

        # TEMPERATURE
        WeatherIconLayoutGrid.addWidget(WeatherTemperature, 0, 1)

        WeatherInsideLayoutGrid.addLayout(WeatherIconLayoutGrid, 0, 0, 4, 1)
        #####################################
        ##################################### Currency
        CurrencyLayout = QGroupBox("Курс валют")
        layout.addWidget(CurrencyLayout, 0, 1)

        CurrencyLayoutInnerGrid = QGridLayout()
        CurrencyLayout.setLayout(CurrencyLayoutInnerGrid)

        if data['currency']['error'] is not None:
            USD = QLabel("Error")
            EUR = QLabel("Error")
        else:
            USD = QLabel(str(data['currency']['USD2RUB']))
            EUR = QLabel(str(data['currency']['EUR2RUB']))

        USD.setFont(QFont('Arial', 12))
        EUR.setFont(QFont('Arial', 12)) 

        USD_LABEL = QLabel("USD/RUB")
        USD_LABEL.setFont(QFont('Arial', 12))

        EUR_LABEL = QLabel("EUR/RUB")
        EUR_LABEL.setFont(QFont('Arial', 12))

        CurrencyLayoutInnerGrid.addWidget(USD_LABEL, 0, 0)
        CurrencyLayoutInnerGrid.addWidget(EUR_LABEL, 1, 0)

        CurrencyLayoutInnerGrid.addWidget(USD, 0, 1)
        CurrencyLayoutInnerGrid.addWidget(EUR, 1, 1)
        #####################################
        ##################################### Main news
        MainNewsLayout = QGroupBox("Главные новости")
        layout.addWidget(MainNewsLayout, 1, 0, 1, 2)
        
        MainNewsInnerLayout = QVBoxLayout()
        MainNewsLayout.setLayout(MainNewsInnerLayout)
        if data['main_news']['error'] is None:
            for i in range(len(data['main_news']['news'])):
                tempMainNews = QLabel(data['main_news']['news'][i]['label'])
                tempMainNews.setFont(QFont('Arial', 10))
                MainNewsInnerLayout.addWidget(tempMainNews)
        else:
            tempMainNews = QLabel("Error")
            tempMainNews.setFont(QFont('Arial', 12))
            MainNewsInnerLayout.addWidget(tempMainNews)
        #####################################

        self.setLayout(layout)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.Popup)
        self.setGeometry(coords[0] - WIDTH//2, coords[1] - HEIGHT, WIDTH, HEIGHT)

# class Settings(QWidget):
#     def __init__(self, coords):
#         super().__init__()
#         layout = QVBoxLayout()
#         self.label = QLabel("Settings")
#         layout.addWidget(self.label)

#         self.setLayout(layout)

#         self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
#         self.setWindowFlags(QtCore.Qt.Popup)

#         self.setGeometry(coords[0] - WIDTH//2, coords[1] - HEIGHT, WIDTH, HEIGHT)


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

        updateAction.triggered.connect(self.UpdateData)
        settingAction.triggered.connect(self.ShowSettings)
        exitAction.triggered.connect(self.Destructor)

        self.UpdateIcon()
        self.activated.connect(self.ShowNewWindow)
        self.flag = False

    def ShowSettings(self):
        global up
        AskForData()
        up.PreviousTime = -1

    def Destructor(self, reason):
        global up
        up.stop()
        QtWidgets.qApp.quit()

    def ShowNewWindow(self, reason):
        if reason == self.Trigger:
            currCoords = self.geometry().getRect()
            if self.w is None:
                self.w = MainWindow(currCoords)
            else:
                self.w.setGeometry(currCoords[0] - WIDTH//2, currCoords[1] - HEIGHT, WIDTH, HEIGHT)
            self.w.show()

    def UpdateData(self):
        global up
        up.PreviousTime = -1
        self.UpdateIcon()

    def UpdateIcon(self):
        global ICON_IMAGE
        try:
            timer = QtCore.QTimer()
            timer.timeout.connect(self.UpdateIcon)
            timer.start(userData.get("icon_update_timeout", 1000))
            
            if ICON_IMAGE is None:
                icone = "resources/icons/icon.ico"
            else:
                image = PQ.ImageQt(ICON_IMAGE)
                pixmap = QPixmap.fromImage(image)
                icone = QIcon(pixmap)
            
            self.setIcon(QtGui.QIcon(icone))
        finally:
            QtCore.QTimer.singleShot(userData.get("icon_update_timeout", 1000), self.UpdateIcon)

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


appIcon = QtWidgets.QApplication(sys.argv)
# qtmodern.styles.dark(appIcon)
appIcon.setStyle("Fusion")
if userData.get("theme", "dark") == "dark":
    appIcon.setPalette(DarkTheme())

wIcon = QtWidgets.QWidget()
trayIcon = SystemTrayIcon(QtGui.QIcon("resources/icons/icon.ico"), wIcon)
trayIcon.show()

sys.exit(appIcon.exec_())
