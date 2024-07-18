from datetime import datetime

from bs4 import BeautifulSoup

from base import (
    BaseSystem,
    Credential,
    Transaction,
    Station,
    Point,
)


class GasStationSystem(BaseSystem):
    base_url: str = "https://test-app.avtoversant.ru"
    stations: dict[str, dict] = {}

    def auth(self, credential: Credential) -> None:
        self.base_url = credential.url or self.base_url
        login_url = f"{self.base_url}/account/login"

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-Winter-Request-Handler": "onSignin",
        }

        data = {
            "login": credential.login,
            "password": credential.password,
            "remember": 1,
        }

        self._get_response(
            "post", login_url, skip_credential=True, json=data, headers=headers
        )

        super().auth(credential)

    def save_stations(self) -> None:
        """
        Получает все станции и возвращает их в виде словаря
        Ключ - id станции
        Значение - словарь с данными о станции
        """
        stations_url = f"{self.base_url}/abakam/gasstations/stations"
        response = self._get_response("get", stations_url)
        stations = response.json()
        self.stations = {str(station["id"]): station for station in stations}

    def get_transactions(
        self, from_date: datetime, to_date: datetime
    ) -> list[Transaction]:
        self.save_stations()
        transactions: list[Transaction] = []
        transactions_url = f"{self.base_url}/account/transactions?page_size=100"

        data = {
            "start_date": str(from_date.date()),
            "start_time": str(from_date.time()),
            "end_date": str(to_date.date()),
            "end_time": str(to_date.time()),
        }

        response = self._get_response("post", transactions_url, json=data)
        soup = BeautifulSoup(response.text, "lxml")
        count_pages = self._extract_page_count(soup)

        for page in range(1, count_pages + 1):
            data["page"] = page

            response = self._get_response("post", transactions_url, json=data)
            soup = BeautifulSoup(response.text, "lxml")
            rows = soup.find_all("tr")

            for row in rows:
                if "Пополнение" in row.text:
                    continue

                transaction = self._parse_transaction_row(row)
                if transaction:
                    transactions.append(transaction)

        return transactions

    @staticmethod
    def _extract_page_count(soup: BeautifulSoup) -> int:
        page_elements = soup.find_all("li", {"class": "page-item"})
        # Если транзакций за выбранный период нет, то не будет пагинации
        if not page_elements:
            return 1
        return int(page_elements[-2].get_text(strip=True))

    def _parse_transaction_row(self, row: BeautifulSoup) -> Transaction | None:
        (
            transaction_id,
            date_str,
            contract,
            card,
            station_code,
            service,
            volume,
            transaction_sum,
        ) = (td.get_text(strip=True) for td in row.find_all("td"))

        contracts = self.credential.contracts
        if contracts and contract not in contracts:
            # Если транзакция не подходит под выбранные контракты
            return None

        station_dict = self.stations.get(station_code)
        if not station_dict:
            # Станция может быть удалена и не отображаться на карте leaflet
            return None

        point = Point(lat=station_dict.get("lat"), lng=station_dict.get("lng"))

        station = Station(
            code=station_code,
            point=point,
            name=station_dict.get("name"),
            brand=station_dict.get("brand"),
            address=station_dict.get("address"),
        )

        return Transaction(
            credential=self.credential,
            station=station,
            card=card,
            code=transaction_id,
            date=datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S"),
            service=service,
            sum=float(transaction_sum),
            volume=float(volume),
        )
