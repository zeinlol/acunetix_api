import json
from typing import NoReturn

import requests

from api.classes.target import AcunetixTarget
from api.core import AcunetixCoreAPI
from core.tools import timed_print


class AcunetixAPI(AcunetixCoreAPI):

    def __init__(self, username: str, password: str, host: str, port: int, secure: bool):
        super().__init__(username=username, password=password, host=host, port=port, secure=secure)
        self.test_connection()
        self._login()
        self.update_profile()

    def update_profile(self) -> NoReturn:
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
        resp = self._patch_request(path='me', data=data)
        if resp.status_code == 204:
            timed_print('User profile changed successfully. The current language is: English.')
        else:
            timed_print('User profile settings have not been changed. Something went wrong.\n'
                        f'Info: {resp.text} Status code: {resp.status_code}. Content: {resp.content}')
            exit(1)

    def create_target(self, address, **kwargs) -> AcunetixTarget:  # todo check valid?
        """Create target for scanning process.
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
        request = self._post_request(path='targets', data=data)
        if request.status_code != 201:
            timed_print(f'Fail to create target for the address: {address}.\n'
                        f'Info: {request.text} Status code: {request.status_code}. Content: {request.content}'
                        f'\nExit')
            exit(1)
        target_json = request.json()
        target = AcunetixTarget(
            address=target_json['address'],
            fqdn=target_json['fqdn'],
            domain=target_json['domain'],
            general_type=target_json.get('type', 'default') or 'default',  # can be None
            target_type=target_json.get('target_type', 'default') or 'default',  # can be None
            target_id=target_json['target_id'],
            description=target_json.get('description', ''),
            criticality=target_json.get('criticality', 10),
        )
        timed_print(f'Target {target} for the address: {address} has been successfully created.')
        return target

    def run_scan(self, target_id: str, profile_id: str = None, **kwargs) -> requests.Response:
        """Starts the scanning process.

        Args:
            target_id: The target identifier.
            profile_id: The profile identifier displays in which mode the scan will be performed.
                You can find identifiers here:
                    http://wp.blkstone.me/wp-content/uploads/2019/11/Acunetix-API-Documentation.html#get-scans

        """
        template_id = kwargs.get('report_template_id') or '11111111-1111-1111-1111-111111111126'  # Comprehensive (new)
        scan_data = {
            'target_id': target_id,
            'profile_id': profile_id or '11111111-1111-1111-1111-111111111111',  # Full Scan
            'report_template_id': template_id,
            'schedule': {
                'disable': kwargs.get('disable') or False,
                'start_date': kwargs.get('start_date'),  # can be None
                'time_sensitive': kwargs.get('time_sensitive') or False
            }
        }
        data = json.dumps(scan_data)
        return self._post_request(path='scans', data=data)

    def get_scans(self) -> requests.Response:
        """Get all available scans..
        """

        return self._get_request('scans')

    def get_scan(self, scan_id: str) -> requests.Response:
        """Get a specific scan.

        Args:
            scan_id: The scan identifier.

        """

        return self._get_request(f'scans/{scan_id}')

    def get_reports(self) -> requests.Response:
        """Get all available reports..
        """

        return self._get_request('reports')

    def download_report(self, descriptor: str) -> requests.Response:
        """Configures proxy settings for a target.

        Args:
            descriptor: The report identifier.

        """
        return self._get_request(path=f'reports/download/{descriptor}')
