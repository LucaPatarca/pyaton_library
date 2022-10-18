import json
from requests import post, get

HOST = "https://www.atonstorage.com/atonTC/"


class NoAuth(Exception):
    pass


class AuthFailed(Exception):
    pass


class CommunicationFailed(Exception):
    pass


class AtonStorage:
    def __init__(self, username=None, sn=None, id_impianto=None) -> None:
        self.username = username
        self.sn = sn
        self.id_impianto = id_impianto
        self.interval = 30

        self.current_battery_status = None
        self.current_house_consumption = None
        self.current_solar_production = None
        self.current_battery_power = None
        self.current_grid_power = None

        self.grid_to_house = None
        self.solar_to_battery = None
        self.solar_to_grid = None
        self.battery_to_house = None
        self.solar_to_house = None
        self.grid_to_battery = None
        self.battery_to_grid = None

    def authenticate(self, username, password) -> bool:
        resp = post(
            HOST + "index.php",
            data={"username": username, "password": password},
            timeout=5,
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

        if sn and id_impianto > 0:
            self.id_impianto = str(id_impianto)
            self.sn = sn
            self.username = username

            return True

        return False

    def fetch_data(self):
        res = get(
            HOST + "set_request.php",
            params={"sn": self.sn, "request": "MONITOR", "intervallo": self.interval},
            timeout=5,
        )
        if res.status_code != 200 or res.text != "ok":
            raise CommunicationFailed("Cannot send monitor command")
        res = get(HOST + "get_monitor.php", params={"sn": self.sn}, timeout=5)
        if res.status_code != 200:
            raise CommunicationFailed("Cannot get status from api")
        data = json.loads(res.text)

        self.current_battery_status = data["soc"]
        self.current_house_consumption = data["pUtenze"]
        self.current_battery_power = data["pBatteria"]
        self.current_solar_production = data["pSolare"]
        self.current_grid_power = data["pRete"]

        self.grid_to_house = int(data["status"]) & 1 == 1
        self.solar_to_battery = int(data["status"]) & 2 == 2
        self.solar_to_grid = int(data["status"]) & 4 == 4
        self.battery_to_house = int(data["status"]) & 8 == 8
        self.solar_to_house = int(data["status"]) & 16 == 16
        self.grid_to_battery = int(data["status"]) & 32 == 32
        self.battery_to_grid = int(data["status"]) & 64 == 64

    def test_connection(self) -> bool:
        return True

