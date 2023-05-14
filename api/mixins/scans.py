import json
from typing import TYPE_CHECKING

from api import constants
from api.classes.scan import AcunetixScan

if TYPE_CHECKING:
    from api.base import AcunetixAPI


class ScanMixin:

    def get_scans(self: "AcunetixAPI") -> list[AcunetixScan]:
        """Get all available scans..."""
        request = self._get_request('scans')
        return [self.parse_scan(created_scan=scan) for scan in request.json().get('scans', [])]

    def get_scan(self: "AcunetixAPI", scan_id: str) -> AcunetixScan:
        request = self._get_request(f'scans/{scan_id}')
        return self.parse_scan(created_scan=request.json())

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

    def run_scan(self: "AcunetixAPI",
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
