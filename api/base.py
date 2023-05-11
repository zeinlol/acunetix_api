import json
from typing import NoReturn

import requests

from api import constants
from api.classes.report import AcunetixReport
from api.classes.scan import AcunetixScan
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

    def create_target(self, address, **kwargs) -> AcunetixTarget:
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

    def run_scan(self,
                 target_id: str,
                 profile_id: str = constants.DEFAULT_PROFILE_ID,
                 report_template_id: str = constants.DEFAULT_REPORT_TEMPLATE_ID,
                 disable: bool = False,
                 time_sensitive: bool = False,
                 start_date: str = None, ) -> AcunetixScan:
        scan_data = {
            'target_id': target_id,
            'profile_id': profile_id,
            'report_template_id': report_template_id,
            'schedule': {
                'disable': disable,
                'start_date': start_date,
                'time_sensitive': time_sensitive,
            }
        }
        data = json.dumps(scan_data)
        request = self._post_request(path='scans', data=data)
        created_scan = request.json()
        return self.parse_scan(created_scan=created_scan)

    def get_scans(self) -> requests.Response:
        """Get all available scans..
        """

        return self._get_request('scans')

    def get_scan(self, scan_id: str) -> AcunetixScan:
        request = self._get_request(f'scans/{scan_id}')
        created_scan = request.json()
        return self.parse_scan(created_scan=created_scan)

    @staticmethod
    def parse_scan(created_scan: dict) -> AcunetixScan:
        return AcunetixScan(
            current_session=created_scan.get('current_session', {}),
            profile_id=created_scan['profile_id'],
            scan_id=created_scan['scan_id'],
            target_id=created_scan['target_id'],
            target=created_scan.get('target', {}),
            report_template_id=created_scan['report_template_id'],
            profile_name=created_scan.get('profile_name', ''),
            next_run=created_scan.get('next_run', ''),
            max_scan_time=created_scan['max_scan_time'],
            incremental=created_scan['incremental'],
            criticality=created_scan.get('criticality', 10),
        )

    def get_reports(self, target_id: str = None) -> list[AcunetixReport]:
        """Get all available reports..."""
        path = 'reports'
        if target_id:
            path = f'{path}?target={target_id}'
        timed_print(f'Get reports from {path}')
        response = self._get_request(path=path)
        timed_print(f'Get reports response {response.status_code}')
        return [
            AcunetixReport(
                download=report['download'],
                generation_date=report['generation_date'],
                report_id=report['report_id'],
                template_id=report['template_id'],
                template_name=report['template_name'],
                template_type=report['template_type'],
                status=report['status'],
                source=report['source'],
            )
            for report in response.json().get('reports')
        ]

    def download_report(self, descriptor: str) -> requests.Response:
        """Configures proxy settings for a target.

        Args:
            descriptor: The report identifier.

        """

        timed_print(f'Downloading report {descriptor}')
        return self._get_request(path=f'reports/download/{descriptor}')
