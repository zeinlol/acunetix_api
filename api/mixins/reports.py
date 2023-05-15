import json
from typing import TYPE_CHECKING

import requests

from api.classes.report import AcunetixReport
from core.tools import timed_print

if TYPE_CHECKING:
    from api.base import AcunetixAPI


class ReportMixin:
    def get_reports(self: "AcunetixAPI", target_id: str = None) -> list[AcunetixReport]:
        """Get all available reports..."""
        path = 'reports'
        response = self._get_request(path=path)
        # timed_print(f'Get reports response {response.status_code}')
        reports = [
            self.parse_report(created_report=report)
            for report in response.json().get('reports')
        ]
        if target_id:
            return list(filter(lambda report: (target_id in report.source.id_list), reports))
        return reports

    def download_report(self: "AcunetixAPI", descriptor: str) -> requests.Response:
        """Configures proxy settings for a target.

        Args:
            descriptor: The report identifier.

        """

        timed_print(f'Downloading report {descriptor}')
        return self._get_request(path=f'reports/download/{descriptor}')

    def run_scan_report(self: "AcunetixAPI", scan_id: str, template_id: str) -> AcunetixReport:
        data = {
            "template_id": template_id,
            "source": {
                "id_list": [
                    scan_id
                ],
                "list_type": "scan_result"
            }
        }
        data = json.dumps(data)
        export = self._post_request(path='reports', data=data)
        # timed_print(export.json())
        return self.parse_report(created_report=export.json())

    def get_report(self: "AcunetixAPI", report_id: str) -> AcunetixReport:
        request = self._get_request(f'reports/{report_id}')
        return self.parse_report(created_report=request.json())

    @staticmethod
    def parse_report(created_report: dict) -> AcunetixReport:
        return AcunetixReport(
            download=created_report['download'],
            generation_date=created_report['generation_date'],
            report_id=created_report['report_id'],
            template_id=created_report['template_id'],
            template_name=created_report['template_name'],
            template_type=created_report['template_type'],
            status=created_report['status'],
            source=created_report.get('source', []),
        )

    def delete_report(self: "AcunetixAPI", report: AcunetixReport):
        self._delete_request(path=f'reports/{report.report_id}')
