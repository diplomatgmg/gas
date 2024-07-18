from datetime import datetime

from base import BaseSystem, Credential, Transaction, InvalidCredentialsError


class GasStationSystem(BaseSystem):
    base_url: str = "https://test-app.avtoversant.ru"

    def auth(self, credential: Credential) -> None:
        url = credential.url or self.base_url
        login_url = f"{url}/account/login"

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

    def get_transactions(
        self, from_date: datetime, to_date: datetime
    ) -> list[Transaction]:
        raise NotImplementedError()
