import json
import time
from urllib.parse import urlparse

from api.base import AcunetixAPI
from api.classes.export import AcunetixExportReport
from api.classes.scan_status import FINAL_ACUNETIX_STATUSES, AcunetixScanStatuses
from api.classes.target import AcunetixTarget
from api.constants import ExportTypes
from core import report_html_parser
from core.tools import timed_print


class Analyze:
    def __init__(self, address: str, api: AcunetixAPI, output_file: str, proxy: str | None = None):
        self.current_scan = None
        self.scan_report: AcunetixExportReport | None = None
        self.address = address
        self.api = api
        self.target = self.init_target()
        self.output_file = output_file
        if proxy:
            self.init_proxy(proxy)

    def init_target(self) -> AcunetixTarget:
        return self.api.create_target(self.address)

    def init_proxy(self, proxy: str) -> None:
        proxy = urlparse(proxy)
        timed_print(f'Set up a proxy configuration with host: {proxy.hostname} and port: {proxy.port}')
        self.api.setup_proxy_configuration(target_id=self.target.target_id,
                                           host=str(proxy.hostname),
                                           port=proxy.port,
                                           protocol=proxy.scheme)

    def run_scan_and_get_report(self) -> None:
        self.current_scan = self.api.run_scan(target_id=self.target.target_id)
        timed_print(f'The scan: {self.current_scan.scan_id} was created successfully. Wait for the scan to complete.')
        status = self.wait_for_finishing_scan()
        if status != AcunetixScanStatuses.COMPLETED.value:
            self.exit_with_error(message=f'Target scan was not competed and finished with status: {status}.')
        timed_print('Checking reports...')
        self.scan_report = self.api.run_scan_export(scan_id=self.current_scan.scan_id, export_id=ExportTypes.JSON.value)
        report_status = self.wait_for_finishing_report()
        if report_status != AcunetixScanStatuses.COMPLETED.value:
            self.exit_with_error(message=f'Scan was completed successfully, but export finished with status: {status}.')
        self.download_report(report_name=self.scan_report.download_json_name, output_file=self.output_file)
        # self.work_with_report_for_targets()
        timed_print('Exiting...')
        exit(0)

    def exit_with_error(self, message: str):
        with open(self.output_file, 'w') as f:
            json.dump({'failed': message}, f, indent=4)
        timed_print(message)
        exit(1)

    def wait_for_finishing_scan(self) -> "AcunetixScanStatuses.value":
        while True:
            scan = self.api.get_scan(scan_id=self.current_scan.scan_id)
            if scan.current_session.status in FINAL_ACUNETIX_STATUSES:
                timed_print(f'Scanning ended with status: {scan.current_session.status.title()}.')
                break
            else:
                timed_print(f'The current scan status is: {scan.current_session.status.title()}.')
            time.sleep(30)
        return scan.current_session.status

    def wait_for_finishing_report(self) -> "AcunetixScanStatuses.value":
        while True:
            report = self.api.get_export(export_id=self.scan_report.report_id)
            if report.status in FINAL_ACUNETIX_STATUSES:
                timed_print(f'Export generated with status: {report.status.title()}.')
                break
            else:
                timed_print(f'The current export status is: {report.status.title()}.')
            time.sleep(30)
        return report.status

    def download_report(self, report_name: str, output_file: str):
        report_file = self.api.download_report(descriptor=report_name)
        timed_print('Report received')
        with open(output_file, 'w') as f:
            f.write(report_file.text)
            timed_print(f'Results saved to {output_file}')

    def work_with_report_for_targets(self):
        report_generated = False
        while not report_generated:
            reports = self.api.get_reports(target_id=self.target.target_id)
            timed_print(f'Reports received. Amount of valid reports: {len(reports)}')
            if not reports:
                timed_print('No reports. Wait for generation')
                time.sleep(10)
                continue
            report = reports[-1]  # get only one report
            if report.status != AcunetixScanStatuses.PROCESSING.value:
                timed_print('Report is still generating. Wait for competing')
                time.sleep(10)
                continue
            if report.status != AcunetixScanStatuses.COMPLETED.value:
                self.exit_with_error(message='Error while generating report.')
            report_generated = True
            self.download_report(report_name=report.download_html_name, output_file=report.download_html_name)
            report_html_parser.parse_html(file_absolute_path=report.download_html_name, output_file=self.output_file)
