import json
from abc import ABC
from typing import NoReturn

from api.core import AcunetixCoreAPI
from api.mixins.exports import ExportsMixin
from api.mixins.reports import ReportMixin
from api.mixins.scans import ScanMixin
from api.mixins.targets import TargetMixin
from core.tools import timed_print


class AcunetixAPI(AcunetixCoreAPI,
                  TargetMixin,
                  ScanMixin,
                  ReportMixin,
                  ExportsMixin,
                  ABC):

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
