import json
from typing import TYPE_CHECKING

from api.classes.export import AcunetixExportReport

if TYPE_CHECKING:
    from api.base import AcunetixAPI


class ExportsMixin:

    def run_scan_export(self: "AcunetixAPI", scan_id: str, export_id: str) -> AcunetixExportReport:
        data = {
            "export_id": export_id,
            "source": {
                "id_list": [
                    scan_id
                ],
                "list_type": "scan_result"
            }
        }
        data = json.dumps(data)
        export = self._post_request(path='exports', data=data)
        # timed_print(export.json())
        return self.parse_export(created_export=export.json())

    def get_export(self: "AcunetixAPI", export_id: str) -> AcunetixExportReport:
        request = self._get_request(f'exports/{export_id}')
        created_export = request.json()
        return self.parse_export(created_export=created_export)

    @staticmethod
    def parse_export(created_export: dict) -> AcunetixExportReport:
        return AcunetixExportReport(
            download=created_export['download'],
            generation_date=created_export['generation_date'],
            report_id=created_export['report_id'],
            template_id=created_export['template_id'],
            template_name=created_export['template_name'],
            template_type=created_export['template_type'],
            status=created_export['status'],
            source=created_export.get('source', []),
        )
