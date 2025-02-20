from datetime import datetime

from bs4 import BeautifulSoup

from base import (
    BaseSystem,
    Credential,
    Transaction,
    InvalidCredentialsError,
    Station,
    Point,
)


class GasStationSystem(BaseSystem):
    base_url: str = "https://test-app.avtoversant.ru"

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

        response = self.connection.post(login_url, json=data, headers=headers)

        if response.status_code != 200:
            raise InvalidCredentialsError()

        super().auth(credential)

    def get_stations(self) -> dict[str, dict]:
        """
        Получает все станции и возвращает их в виде словаря
        Ключ - id станции
        Значение - словарь с данными о станции
        """
        stations_url = f"{self.base_url}/abakam/gasstations/stations"
        response = self.connection.get(stations_url)
        stations = response.json()
        stations_dict = {str(station["id"]): station for station in stations}
        return stations_dict

    def get_transactions(
        self, from_date: datetime, to_date: datetime
    ) -> list[Transaction]:
        stations = self.get_stations()
        transactions: list[Transaction] = []
        transactions_url = f"{self.base_url}/account/transactions?page_size=100"

        data = {
            "start_date": str(from_date.date()),
            "start_time": str(from_date.time()),
            "end_date": str(to_date.date()),
            "end_time": str(to_date.time()),
        }

        response = self.connection.post(transactions_url, json=data)
        soup = BeautifulSoup(response.text, "html.parser")

        page_elements = soup.find_all("li", {"class": "page-item"})
        # Если транзакций за выбранный период нет, то не будет пагинации
        if not page_elements:
            count_pages = 1
        else:
            count_pages = int(page_elements[-2].get_text(strip=True))

        for page in range(1, count_pages + 1):
            data["page"] = page

            response = self.connection.post(transactions_url, json=data)
            soup = BeautifulSoup(response.text, "html.parser")

            rows = soup.find_all("tr")

            for row in rows:
                if "Пополнение" in row.text:
                    continue

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
                    continue

                station_dict = stations.get(station_code)

                if not station_dict:
                    # Станция может быть удалена и не отображаться на карте leaflet
                    continue

                point = Point(lat=station_dict.get("lat"), lng=station_dict.get("lng"))
                station = Station(
                    code=station_code,
                    name=station_dict.get("name"),
                    brand=station_dict.get("brand"),
                    point=point,
                    address=station_dict.get("address"),
                )

                transaction = Transaction(
                    credential=self.credential,
                    station=station,
                    card=card,
                    code=transaction_id,
                    date=datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S"),
                    service=service,
                    sum=float(transaction_sum),
                    volume=float(volume),
                )

                transactions.append(transaction)

        return transactions
