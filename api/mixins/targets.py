import json
import time
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
        if self.is_use_fake_client:
            while True:
                response = self._post_request(path='targets', data=data)
                if target_id := response.json().get('target_id', None):
                    timed_print(f'[Fake Client] Target already added. Target ID: {target_id}')
                    return self.get_target(target_id=target_id)
                queue_order = response.json().get('order', None)
                if not queue_order or queue_order > 0:
                    timed_print(f'[Fake Client] Target is in queue. Order: {queue_order}')
                    time.sleep(30)
        else:
            response = self._post_request(path='targets', data=data)
            if response.status_code != 201:
                timed_print(f'Fail to create target for the address: {address}.\n'
                            f'Info: {response.text} Status code: {response.status_code}. Content: {response.content}'
                            f'\nExit')
                self.close_session()
                exit(1)
        target = self.parse_target(target_dict=response.json())
        timed_print(f'Target {target} for the address: {address} has been successfully created.')
        return target

    def get_targets(self: "AcunetixAPI") -> list[AcunetixTarget]:
        response = self._get_request(path='targets')
        targets = response.json().get('targets', [])
        return [self.parse_target(target_dict=target) for target in targets]

    def get_target(self: "AcunetixAPI", target_id: str) -> AcunetixTarget:
        response = self._get_request(path=f'targets/{target_id}')
        return self.parse_target(target_dict=response.json())

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
