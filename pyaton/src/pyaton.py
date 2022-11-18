import json
from requests import post, get
import datetime
from fake_useragent import UserAgent

HOST = "https://www.atonstorage.com/atonTC/"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

class APIStatus:
    """Represents the status of a solar panel array"""
    def __init__(self) -> None:
        self.battery_status = 0
        self.house_consumption = 0
        self.solar_production = 0
        self.battery_power = 0
        self.grid_power = 0

        self.is_grid_to_house = False
        self.is_solar_to_battery = False
        self.is_solar_to_grid = False
        self.is_battery_to_house = False
        self.is_solar_to_house = False
        self.is_grid_to_battery = False
        self.is_battery_to_grid = False

        self.grid_to_house = 0
        self.solar_to_battery = 0
        self.solar_to_grid = 0
        self.battery_to_house = 0
        self.solar_to_house = 0
        self.grid_to_battery = 0
        self.battery_to_grid = 0

        self.last_update = datetime.datetime.min

        self.sold_energy = 0
        self.solar_energy = 0
        self.self_consumed_energy = 0
        self.bought_energy = 0

        self.house_voltage = 0.0
        self.grid_voltage = 0.0
        self.grid_frequency = 0.0

    def update(self, json) -> None:
        self.battery_status = float(json["soc"])
        self.house_consumption = int(json["pUtenze"])
        self.battery_power = int(json["pBatteria"])
        self.solar_production = int(json["pSolare"])
        self.grid_power = int(json["pRete"])

        self.is_grid_to_house = int(json["status"]) & 1 == 1
        self.is_solar_to_battery = int(json["status"]) & 2 == 2
        self.is_solar_to_grid = int(json["status"]) & 4 == 4
        self.is_battery_to_house = int(json["status"]) & 8 == 8
        self.is_solar_to_house = int(json["status"]) & 16 == 16
        self.is_grid_to_battery = int(json["status"]) & 32 == 32
        self.is_battery_to_grid = int(json["status"]) & 64 == 64

        if(self.is_solar_to_grid):
            pass
        if(self.is_solar_to_house):
            pass
        if(self.is_solar_to_battery):
            pass
        if(self.is_grid_to_house):
            pass
        if(self.is_grid_to_battery):
            pass
        if(self.is_battery_to_house):
            pass
        if(self.is_battery_to_grid):
            pass

        self.last_update = datetime.datetime.strptime(json["data"], DATETIME_FORMAT).isoformat()

        self.sold_energy = int(json["eVenduta"])
        self.solar_energy = int(json["ePannelli"])
        self.self_consumed_energy = int(json["eBatteria"])
        self.bought_energy = int(json["eComprata"])

        self.house_voltage = float(json["utenzeV"])
        self.grid_voltage = float(json["gridV"])
        self.grid_frequency = float(json["gridHz"])

    @property
    def consumed_energy(self) -> int:
        return self.bought_energy + self.self_consumed_energy

    @property
    def self_sufficiency(self) -> int:
        return 100 - ((self.bought_energy / self.consumed_energy) * 100)


class NoAuth(Exception):
    """User did not authenticate before using the API"""


class AuthFailed(Exception):
    """Authentication failed"""


class CommunicationFailed(Exception):
    """Cannot communicate with the server"""


class AtonAPI:
    def __init__(self, username=None, sn=None, id_impianto=None) -> None:
        self.username = username
        self.sn = sn
        self.id_impianto = id_impianto
        self.cookies = None
        self.interval = 30
        self.user_agent = UserAgent()
        self.status = APIStatus()

    def authenticate(self, username, password) -> bool:
        """Tries to authenticate the user and saves all user specific data to this class"""
        resp = post(
            HOST + "index.php",
            data={"username": username, "password": password},
            timeout=15,
            allow_redirects=False,
        )
        if resp.status_code != 200:
            return False

        sn_start = resp.text.find("var sn")
        sn_start = resp.text.find('"', sn_start, sn_start + 30) + 1
        sn_end = resp.text.find('"', sn_start + 1, sn_start + 50)
        sn = resp.text[sn_start:sn_end]

        id_impianto_start = resp.text.find("var idImpianto")
        id_impianto_start = (
            resp.text.find("=", id_impianto_start, id_impianto_start + 30) + 1
        )
        id_impianto_end = resp.text.find(
            ";", id_impianto_start + 1, id_impianto_start + 50
        )
        id_impianto = resp.text[id_impianto_start:id_impianto_end]
        id_impianto = int(id_impianto)

        if sn and id_impianto > 0 and len(resp.cookies) > 0:
            self.id_impianto = str(id_impianto)
            self.sn = sn
            self.username = username
            self.cookies = resp.cookies

            return True

        return False

    def fetch_data(self):
        """Fetches the current status from the website and saves it in this class status"""
        ua = self.user_agent.random
        headers = {
            'User-Agent': ua,
        }
        res = get(
            HOST + "set_request.php",
            params={"sn": self.sn, "request": "MONITOR", "intervallo": self.interval},
            timeout=15,
            cookies=self.cookies,
            headers=headers,
        )
        if res.status_code == 401:
            raise NoAuth("Re-authentication needed")
        if res.status_code != 200 or res.text != "ok":
            raise CommunicationFailed("Cannot send monitor command")
        res = get(
            HOST + "get_monitor.php",
            params={"sn": self.sn},
            timeout=15,
            cookies=self.cookies,
            headers=headers,
        )
        if res.status_code == 401:
            raise NoAuth("Re-authentication needed")
        if res.status_code != 200:
            raise CommunicationFailed("Cannot get status from api")
        data = json.loads(res.text)
        self.status.update(data)

    def test_connection(self) -> bool:
        return True

