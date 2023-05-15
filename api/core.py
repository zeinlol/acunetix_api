import hashlib
import json
from typing import NoReturn

import requests
import urllib3

from core.tools import timed_print


class AcunetixCoreAPI:

    def __init__(self, username: str, password: str, host: str, port: int, secure: bool):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.secure = secure
        self.session = self._init_session()

    @property
    def headers_json(self) -> dict:
        return {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
            'Accept': "application/json, text/plain, */*",
            'Accept-Language': "es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3",
            'Accept-Encoding': "gzip, deflate, br",
            'Connection': "keep-alive",
            'Content-type': 'application/json',
            'cache-control': "no-cache",
        }

    @property
    def is_logged(self) -> bool:
        return self._get_request('me').status_code == 200

    @property
    def api_url(self) -> str:
        return f'https://{self.host}:{self.port}/api/v1/'

    @property
    def hash_password(self) -> str:
        return hashlib.sha256(self.password.encode()).hexdigest()

    @property
    def auth_data(self) -> str:
        auth_data = {
            'email': self.username,
            'password': self.hash_password,
            'remember_me': True,
            'logout_previous': True,
        }
        return json.dumps(auth_data)

    def _init_session(self) -> requests.Session:
        urllib3.disable_warnings()
        session = requests.Session()
        session.verify = self.secure
        return session

    def _login(self) -> NoReturn:
        self._update_session(headers=self.headers_json)
        response = self._post_request(path='me/login', data=self.auth_data)
        self._update_session(headers=response.headers, cookies=response.cookies)

    def _update_session(self, headers=None, cookies=None) -> NoReturn:
        if headers:
            self.session.headers.update(headers)
        if cookies:
            self.session.cookies.update(cookies)

    def _get_request(self, path: str) -> requests.Response:
        return self.session.get(f'{self.api_url}{path}')

    def _post_request(self, path: str, data) -> requests.Response:
        return self.session.post(f'{self.api_url}{path}', data=data)

    def _patch_request(self, path: str, data) -> requests.Response:
        return self.session.patch(f'{self.api_url}{path}', data=data)

    def _delete_request(self, path: str) -> requests.Response:
        return self.session.delete(f'{self.api_url}{path}')

    def setup_proxy_configuration(self, target_id: str, host: str, port: int, protocol: str) -> NoReturn:
        """Configures proxy settings for a target.

        Args:
            target_id: The target identifier.
            host: The proxy hostname.
            port: The proxy port.
            protocol: The proxy connection protocol.

        """

        config_data = {
            'proxy': {
                'protocol': protocol or 'http',
                'address': host,
                'port': port or 8080,
                'enabled': True
            }
        }
        data = json.dumps(config_data)
        resp = self._patch_request(path=f'targets/{target_id}/configuration', data=data)
        if resp.status_code == 204:
            timed_print('Proxy settings changed successfully.')
        else:
            timed_print(f'Proxy settings have not been changed. Something went wrong. {resp.text}')
            exit(1)

    def test_connection(self) -> NoReturn:
        """Checking the connection to the Acunetix service. The service needs time to initialize.
        Attempts to establish a connection every 10 seconds, the maximum number of attempts is 100.
        """

        counter: int = 0
        while True:
            timed_print(f'Trying to connect to the Acunetix service ({self.api_url})... ')
            try:
                self._get_request('')
            except requests.exceptions.ConnectionError as e:
                counter += 1
                if counter > 10:
                    timed_print('Failed to connect to the Acunetix service.')
                    raise e
                # time.sleep(3)
                continue
            timed_print('The connection to the Acunetix service has been successfully established.')
            break

    def close_session(self):
        self.session.close()
