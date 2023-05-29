import json
import time
from urllib.parse import urlparse

from api.base import AcunetixAPI
from api.classes.export import AcunetixExportReport
from api.classes.report import AcunetixReport
from api.classes.scan import AcunetixScan
from api.classes.scan_status import FINAL_ACUNETIX_STATUSES, AcunetixScanStatuses
from api.classes.target import AcunetixTarget
from core import report_html_parser
from core.tools import timed_print


class Analyze:
    def __init__(self, address: str, api: AcunetixAPI, output_file: str,
                 proxy: str | None = None, demo_mode: bool = False):
        self.current_scan: AcunetixScan | None = None
        self.scan_report: AcunetixExportReport | None = None
        self.address = address
        self.api = api
        self.demo_mode = demo_mode
        self.output_file = output_file
        self.target = self.init_target()
        if proxy:
            self.init_proxy(proxy)

    def init_target(self) -> AcunetixTarget:
        if self.demo_mode:
            all_finished = False
            while not all_finished:
                timed_print('Demo mode is turned on. Checking if all tasks completed...')
                all_finished = self.wait_for_all_scans_are_finished()
                timed_print(f'Demo mode is turned on. Current scan is {"not" if all_finished else ""} allowed')
                if not all_finished:
                    time.sleep(4 * 60)  # sleep 4 minutes
            timed_print('Demo mode is turned on. All previous tasks completed. Start usual scan.')
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
        self.work_with_report_for_targets()
        # self.scan_report = self.api.run_scan_export(scan_id=self.current_scan.current_session.scan_session_id,
        #                                             export_id=ExportTypes.JSON.value)
        # report_status = self.wait_for_finishing_report()
        # if report_status != AcunetixScanStatuses.COMPLETED.value:
        #     self.exit_with_error(message=f'Scan was completed , but export finished with status: {status}.')
        # self.download_report(report_name=self.scan_report.download_json_name, output_file=self.output_file)
        self.exit_application(message='Exiting...')

    def exit_with_error(self, message: str):
        with open(self.output_file, 'w') as f:
            json.dump({'failed': message}, f, indent=4)
        self.exit_application(exit_code=1, message=message)

    def wait_for_finishing_scan(self) -> "AcunetixScanStatuses.value":
        while True:
            scan = self.api.get_scan(scan_id=self.current_scan.scan_id)
            if scan.current_session.status in FINAL_ACUNETIX_STATUSES:
                timed_print(f'Scanning ended with status: {scan.current_session.status.title()}.')
                break
            else:
                timed_print(f'The current scan status is: {scan.current_session.status.title()}.')
            time.sleep(10)
        return scan.current_session.status

    def wait_for_finishing_report(self) -> "AcunetixScanStatuses.value":
        while True:
            report = self.api.get_export(export_id=self.scan_report.report_id)
            if report.status in FINAL_ACUNETIX_STATUSES:
                timed_print(f'Export generated with status: {report.status.title()}.')
                break
            else:
                timed_print(f'The current export status is: {report.status.title()}.')
            time.sleep(10)
        return report.status

    def download_report(self, report_name: str, output_file: str):
        report_file = self.api.download_report(descriptor=report_name)
        timed_print('Report received')
        with open(output_file, 'w') as f:
            f.write(report_file.text)
            timed_print(f'Results saved to {output_file}')

    def work_with_report_for_targets(self):
        # self.scan_report = self.api.run_scan_report(scan_id=self.current_scan.current_session.scan_session_id,
        #                                             template_id=ReportTemplateIds.COMPREHENSIVE.value)
        report_generated = False
        while not report_generated:
            reports = self.api.get_reports(target_id=self.current_scan.current_session.scan_session_id)
            timed_print(f'Reports received. Amount of valid reports: {len(reports)}')
            if not reports:
                timed_print('No reports. Wait for generation')
                time.sleep(10)
                continue
            report = reports[-1]  # get only one report
            # report = self.api.get_report(report_id=self.scan_report.report_id)
            if report.status == AcunetixScanStatuses.PROCESSING.value:
                timed_print('Report is still generating. Wait for competing')
                time.sleep(10)
                continue
            if report.status != AcunetixScanStatuses.COMPLETED.value:
                self.exit_with_error(message='Error while generating report.')
            report_generated = True
            self.download_report(report_name=report.download_html_name, output_file=report.download_html_name)
            report_html_parser.parse_html(file_absolute_path=report.download_html_name, output_file=self.output_file)

    def wait_for_all_scans_are_finished(self) -> bool:
        title = 'DEMO MODE:'
        timed_print(f'{title} check if target exist')
        targets = self.api.get_targets()
        if not targets:
            timed_print(f'{title} No targets. Start usual scan')
            return True
        timed_print(f'{title} {len(targets)} target(s) already exist. Check scans')
        for scan in self.api.get_scans():
            if scan.current_session.status not in FINAL_ACUNETIX_STATUSES:
                timed_print(f'{title} Some scans are still running.')
                return False
        timed_print(f'{title} All scans are finished. Checking reports')
        reports = self.api.get_reports()
        for report in self.api.get_reports():
            if report.status not in FINAL_ACUNETIX_STATUSES:
                timed_print(f'{title} Some reports are still running.')
                return False
        timed_print(f'{title} All reports generated. '
                    f'Wait a while remove old data')
        time.sleep(4*60)
        self.remove_old_data(targets=targets, reports=reports)  # scans automatically removes with targets
        return True

    def remove_old_data(self, targets: list[AcunetixTarget], reports: list[AcunetixReport]) -> None:
        for target in targets:
            self.api.delete_target(target=target)
        for report in reports:
            self.api.delete_report(report=report)
        timed_print('All previous data was removed')
        return

    def remove_current_data(self):
        self.api.delete_target(target=self.target)
        if self.scan_report:
            self.api.delete_report(report=self.scan_report)
        timed_print('Current data removed')

    def exit_application(self, exit_code: int = 0, message: str = 'Exiting application'):
        self.remove_current_data()
        self.api.close_session()
        timed_print(message)
        exit(exit_code)
