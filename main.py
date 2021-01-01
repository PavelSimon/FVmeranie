import sqlite3
from devtools import debug  # výpis premenný do promptu
from config import PORT
from fastapi import FastAPI, Request
# from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import time
# i2c device library and initialisation
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1115 as ADS
import board
import busio
i2c = busio.I2C(board.SCL, board.SDA)

db = sqlite3.connect('meranie.db')
cursor = db.cursor()
try:
    sql = "CREATE TABLE IF NOT EXISTS meranie (CH0 INTEGER, CH0V REAL, CH1 INTEGER, CH1V REAL, CH2 INTEGER, CH2V REAL, CH3 INTEGER, CH3V REAL, poznamka TEXT, cas_merania TEXT NOT NULL)"
    cursor.execute(sql)
except sqlite3.Error as e:
    print("Error:", e.args[0])


def zapis_do_db(db, value0, value1, value2, value3):
    cursor = db.cursor()
    sql = "INSERT INTO meranie VALUES (?,?,?,?,?,?,?,?,'poznámka', datetime('now', 'localtime'))"
    try:
        cursor.execute(sql, (value0.value, value0.voltage, value1.value, value1.voltage,
                             value2.value, value2.voltage, value3.value, value3.voltage))
        db.commit()
    except sqlite3.Error as e:
        print("Error:", e.args[0])
    return db.total_changes


def citanie_z_db(db):
    cursor = db.cursor()
    vystup = ""
    try:
        sql = "SELECT rowid, * FROM meranie"
        cursor.execute(sql)
        vystup = cursor.fetchall()
    except sqlite3.Error as e:
        print("An error occurred:", e.args[0])
    return vystup


def meraj(ads):
    vystup = ""
    value0 = AnalogIn(ads, ADS.P0)
    value1 = AnalogIn(ads, ADS.P1)
    value2 = AnalogIn(ads, ADS.P2)
    value3 = AnalogIn(ads, ADS.P3)

    vystup = [{
        "CH0": value0.value,
        "CH0V": value0.voltage,
        "CH1": value1.value,
        "CH1V": value1.voltage,
        "CH2": value2.value,
        "CH2V": value2.voltage,
        "CH3": value3.value,
        "CH3V": value3.voltage
    }]

    return vystup


def meraj_a_zapis(ads, db):
    vystup = ""
    value0 = AnalogIn(ads, ADS.P0)
    value1 = AnalogIn(ads, ADS.P1)
    value2 = AnalogIn(ads, ADS.P2)
    value3 = AnalogIn(ads, ADS.P3)

    zapis_do_db(db, value0, value1, value2, value3)

    vystup = [{
        "CH0": value0.value,
        "CH0V": value0.voltage,
        "CH1": value1.value,
        "CH1V": value1.voltage,
        "CH2": value2.value,
        "CH2V": value2.voltage,
        "CH3": value3.value,
        "CH3V": value3.voltage
    }]

    return vystup


app = FastAPI()

app.mount("/static", StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")

ads = ADS.ADS1115(i2c)

# Routes:


@app.get("/")
async def root(request: Request):
    """
    Ukáže merania
    """

    meranie = meraj(ads)
    # debug(meranie)
    localtime = time.asctime(time.localtime(time.time()))
    print("/; Čas:", localtime)
    return templates.TemplateResponse("home.html", {"request": request, "meranie": meranie, "time": localtime})


@app.get("/meranie")
async def meranie(request: Request):
    """
    Ukáže merania a zapíše ich do db
    """

    meranie = meraj_a_zapis(ads, db)
    # debug(meranie)
    localtime = time.asctime(time.localtime(time.time()))
    print("/; Čas:", localtime)
    return templates.TemplateResponse("home.html", {"request": request, "meranie": meranie, "time": localtime})


@app.get("/graf")
async def graf(request: Request):
    """
    Zobrazí graf nameranej charakteristiky (zatiaľ iba text)
    """
    data_z_db = citanie_z_db(db)
    localtime = time.asctime(time.localtime(time.time()))
    print("Graf; Čas:", localtime)
    return templates.TemplateResponse("graf.html", {"request": request, "data_z_db": data_z_db, "time": localtime})


# Code for running app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0",
                port=int(PORT), reload=True, debug=True)
