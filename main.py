# database library
import databases
import sqlalchemy
from pydantic import BaseModel

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


"""# SQLAlchemy specific code, as with any other app"""
DATABASE_URL = "sqlite:///./merania.db"
metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL)

zaznam = sqlalchemy.Table(
    "zaznam",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("CH0", sqlalchemy.Float),
    sqlalchemy.Column("CH0V", sqlalchemy.Float),
    sqlalchemy.Column("CH1", sqlalchemy.Float),
    sqlalchemy.Column("CH1V", sqlalchemy.Float),
    sqlalchemy.Column("CH2", sqlalchemy.Float),
    sqlalchemy.Column("CH2V", sqlalchemy.Float),
    sqlalchemy.Column("CH3", sqlalchemy.Float),
    sqlalchemy.Column("CH3V", sqlalchemy.Float),
    sqlalchemy.Column("poznamka", sqlalchemy.String),
    sqlalchemy.Column("cas_merania", sqlalchemy.DateTime),
)


app = FastAPI()

app.mount("/static", StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")

ads = ADS.ADS1115(i2c)

chan = AnalogIn(ads, ADS.P3)
# debug(chan)

# Routes:


@app.get("/")
async def root(request: Request):
    """
    Show dashboard of all ADC meraní
    """
    value0 = AnalogIn(ads, ADS.P0)
    value1 = AnalogIn(ads, ADS.P1)
    value2 = AnalogIn(ads, ADS.P2)
    value3 = AnalogIn(ads, ADS.P3)

    meranie = [{
        "CH0": value0.value,
        "CH0V": value0.voltage,
        "CH1": value1.value,
        "CH1V": value1.voltage,
        "CH2": value2.value,
        "CH2V": value2.voltage,
        "CH3": value3.value,
        "CH3V": value3.voltage
    }]
    # debug(meranie)
    localtime = time.asctime(time.localtime(time.time()))
    print("/; Čas:", localtime)
    return templates.TemplateResponse("home.html", {"request": request, "meranie": meranie, "time": localtime})


@app.get("/graf")
async def graf(request: Request):
    """
    Zobrazí graf nameranej charakteristiky
    """

    localtime = time.asctime(time.localtime(time.time()))
    print("Graf; Čas:", localtime)
    return templates.TemplateResponse("graf.html", {"request": request, "time": localtime})


# Code for running app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0",
                port=int(PORT), reload=True, debug=True)
