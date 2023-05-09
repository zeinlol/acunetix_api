import hashlib
import json
from typing import NoReturn

import requests
import urllib3

from tools import timed_print


class AcunetixAPI:

    def __init__(self, username: str, password: str, host: str, port: int, secure: bool):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.secure = secure
        self.s = self.__init_session()
        self.test_connection()
        self.__login()
        self.__update_profile()

    @property
    def is_logged(self) -> bool:
        return self.__get_request('me').status_code == 200

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

    def __init_session(self) -> requests.Session:
        urllib3.disable_warnings()
        session = requests.Session()
        session.verify = self.secure
        return session

    def __login(self) -> NoReturn:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
            'Accept': "application/json, text/plain, */*",
            'Accept-Language': "es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3",
            'Accept-Encoding': "gzip, deflate, br",
            'Connection': "keep-alive",
            'Content-type': 'application/json',
            'cache-control': "no-cache",
        }
        self.__update_session(headers=headers)
        resp = self.__post_request(path='me/login', data=self.auth_data)
        self.__update_session(headers=resp.headers, cookies=resp.cookies)

    def __update_session(self, headers=None, cookies=None) -> NoReturn:
        if headers:
            self.s.headers.update(headers)
        if cookies:
            self.s.cookies.update(cookies)

    def __update_profile(self) -> NoReturn:
        user_data = {
            'company': 'Example',
            'first_name': 'Administrator',
            'last_name': 'Example',
            'phone': '+53333333335',
            'website': "https://localhost:13443/#/profile",
            'country': 'AF',
            'lang': 'en',
            'time_zone_offset': None,
            'notifications':
                {
                    'monthly_status': False
                }
        }
        data = json.dumps(user_data)
        resp = self.__patch_request(path='me', data=data)
        if resp.status_code == 204:
            timed_print('User profile changed successfully. The current language is: English.')
        else:
            timed_print('User profile settings have not been changed. Something went wrong.')
            exit(1)

    def __get_request(self, path: str) -> requests.Response:
        return self.s.get(f'{self.api_url}{path}')

    def __post_request(self, path: str, data) -> requests.Response:
        return self.s.post(f'{self.api_url}{path}', data=data)

    def __patch_request(self, path: str, data) -> requests.Response:
        return self.s.patch(f'{self.api_url}{path}', data=data)

    def create_target(self, address, **kwargs) -> requests.Response:  # todo check valid?
        """Starts the scanning process.

        Args:
            address: The target address [url, domain, etc.].
            kwargs: The target additional information.

        """

        target_data = {
            'address': address,
            'description': kwargs.get('description') or '',
            'type': kwargs.get('type') or 'default',
            'criticality': kwargs.get('criticality') or 10  # integer
        }
        data = json.dumps(target_data)
        return self.__post_request(path='targets', data=data)

    def run_scan(self, target_id: str, profile_id: str = None, **kwargs) -> requests.Response:
        """Starts the scanning process.

        Args:
            target_id: The target identifier.
            profile_id: The profile identifier displays in which mode the scan will be performed.
                You can find identifiers here:
                    http://wp.blkstone.me/wp-content/uploads/2019/11/Acunetix-API-Documentation.html#get-scans

        """

        scan_data = {
            'target_id': target_id,
            'profile_id': profile_id or '11111111-1111-1111-1111-111111111111',  # Full Scan
            'report_template_id': kwargs.get('report_template_id') or '11111111-1111-1111-1111-111111111126',  # Comprehensive (new)
            'schedule': {
                'disable': kwargs.get('disable') or False,
                'start_date': kwargs.get('start_date'),  # can be None
                'time_sensitive': kwargs.get('time_sensitive') or False
            }
        }
        data = json.dumps(scan_data)
        return self.__post_request(path='scans', data=data)

    def get_scans(self) -> requests.Response:
        """Get all available scans..
        """

        return self.__get_request('scans')

    def get_scan(self, scan_id: str) -> requests.Response:
        """Get a specific scan.

        Args:
            scan_id: The scan identifier.

        """

        return self.__get_request(f'scans/{scan_id}')

    def get_reports(self) -> requests.Response:
        """Get all available reports..
        """

        return self.__get_request('reports')

    def download_report(self, descriptor: str) -> requests.Response:
        """Configures proxy settings for a target.

        Args:
            descriptor: The report identifier.

        """
        return self.__get_request(path=f'reports/download/{descriptor}')

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
        resp = self.__patch_request(path=f'targets/{target_id}/configuration', data=data)
        if resp.status_code == 204:
            timed_print('Proxy settings changed successfully.')
        else:
            timed_print('Proxy settings have not been changed. Something went wrong.')
            exit(1)

    def test_connection(self) -> NoReturn:
        """Checking the connection to the Acunetix service. The service needs time to initialize.
        Attempts to establish a connection every 10 seconds, the maximum number of attempts is 100.
        """

        counter: int = 0
        while True:
            timed_print(f'Trying to connect to the Acunetix service ({self.api_url})... ')
            try:
                self.__get_request('')
            except requests.exceptions.ConnectionError as e:
                counter += 1
                if counter > 10:
                    timed_print('Failed to connect to the Acunetix service.')
                    raise e
                # time.sleep(3)
                continue
            timed_print('The connection to the Acunetix service has been successfully established.')
            break