import time
from datetime import datetime

from base import Credential
from gas_station_system import GasStationSystem


def timeit(function):
    def wrapped(*args, **kwargs):
        start_time = time.perf_counter()
        res = function(*args, **kwargs)
        total = time.perf_counter() - start_time
        print(f"total - {round(total, 2)} seconds")
        return res

    return wrapped


@timeit
def main():
    cred = Credential(
        url="https://test-app.avtoversant.ru",
        login="test",
        password="v78ilRB63Y1b",
        contracts="001,003",
    )
    system = GasStationSystem()
    system.auth(cred)
    transactions = system.get_transactions(
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 7, 1),
    )

    print("Transactions count", len(transactions))

    for tr in transactions[:10]:
        print(tr)


if __name__ == "__main__":
    main()
