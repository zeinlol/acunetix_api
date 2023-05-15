import json
from typing import TYPE_CHECKING

from api.classes.target import AcunetixTarget
from core.tools import timed_print

if TYPE_CHECKING:
    from api.base import AcunetixAPI


class TargetMixin:

    def create_target(self: "AcunetixAPI", address, **kwargs) -> AcunetixTarget:
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
            self.close_session()
            exit(1)
        target = self.parse_target(target_dict=request.json())
        timed_print(f'Target {target} for the address: {address} has been successfully created.')
        return target

    def get_targets(self: "AcunetixAPI") -> list[AcunetixTarget]:
        response = self._get_request(path='targets')
        targets = response.json().get('targets', [])
        targets_ = {'targets': [
            {
                'address': 'https://example.com',
                'continuous_mode': False,
                'criticality': 10,
                'default_scanning_profile_id': None,
                'delete_able': '2023-07-18T03:00:00+03:00',
                'deleted_at': None,
                'description': '', 'fqdn':
                'example.com',
                'fqdn_hash': '9a15c38d4169901a05fb2414dd4251aa',
                'fqdn_status': 'new',
                'fqdn_tm_hash': 'f5c1dad600285fe88b0d1aafda9d5795',
                'issue_tracker_id': None,
                'last_scan_date': '2023-05-15T09:01:26.740103+03:00',
                'last_scan_id': 'ca7aa850-ed7d-4fdf-b3e9-fa03bec7ec9c',
                'last_scan_session_id': 'ad3338b1-0de6-4d8d-b292-1629a20e6757',
                'last_scan_session_status': 'completed',
                'manual_intervention': None,
                'severity_counts': {'high': 0, 'info': 0, 'low': 0, 'medium': 0},
                'target_id': 'ae5fb95e-8baf-4ff6-bdd5-c523da2fa0e9', 'threat': 0, 'type': None,
                'verification': None}],
                    'pagination': {'count': 1, 'cursor_hash': '8f629dd49f910b9202eb0da5d51fdb6e', 'cursors': [None], 'sort': None}}
        return [self.parse_target(target_dict=target) for target in targets]

    @staticmethod
    def parse_target(target_dict: dict) -> AcunetixTarget:
        return AcunetixTarget(
            address=target_dict['address'],
            fqdn=target_dict['fqdn'],
            domain=target_dict.get('domain'),
            general_type=target_dict.get('type', 'default') or 'default',  # can be None
            target_type=target_dict.get('target_type', 'default') or 'default',  # can be None
            target_id=target_dict['target_id'],
            description=target_dict.get('description', ''),
            criticality=target_dict.get('criticality', 10),
        )

    def delete_target(self: "AcunetixAPI", target: AcunetixTarget):
        self._delete_request(path=f'targets/{target.target_id}')
