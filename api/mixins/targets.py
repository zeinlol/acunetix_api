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
