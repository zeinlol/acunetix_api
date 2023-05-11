import json
import time
from urllib.parse import urlparse

from core import report_html_parser
from api.base import AcunetixAPI
from api.classes.scan_status import FINAL_ACUNETIX_STATUSES, AcunetixScanStatuses
from api.classes.target import AcunetixTarget
from core.tools import timed_print


class Analyze:
    def __init__(self, address: str, api: AcunetixAPI, output_file: str, proxy: str | None = None):
        self.current_scan = None
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
            message = f'Target was not competed successfully and finished with status: {status}.'
            with open(self.output_file, 'w') as f:
                json.dump({'failed': message}, f, indent=4)
            timed_print(message)
            exit(1)

        # TODO: export data as json directly from acunetix?
        timed_print('Checking reports...')
        report_generated = False
        iterations = 0
        while not report_generated:
            iterations += 1
            reports = self.api.get_reports(target_id=self.target.target_id)
            timed_print(f'Reports received. Amount of valid reports: {len(reports)}')
            if not reports:
                timed_print('No reports. Wait for generation')
                time.sleep(10)
                continue
            report_generated = True
            report = reports[-1]  # get only one report
            report_file = self.api.download_report(descriptor=report.download_html_name)
            timed_print('Report received')
            with open(report.download_html_name, 'w') as f:
                f.write(report_file.text)
            report_html_parser.parse_html(file_absolute_path=report.download_html_name, output_file=self.output_file)
            if iterations > 20:
                with open(self.output_file, 'w') as f:
                    json.dump({'failed': 'Target scan completed successfully, but report was not generated'}, f)

        timed_print('Exiting...')
        exit(0)

    def wait_for_finishing_scan(self) -> "AcunetixScanStatuses.value":
        while True:
            scan = self.api.get_scan(scan_id=self.current_scan.scan_id)
            status = scan.current_session.status
            if scan.current_session.status in FINAL_ACUNETIX_STATUSES:
                timed_print(f'Scanning ended with status: {scan.current_session.status.title()}.')
                break
            else:
                timed_print(f'The current scan status is: {scan.current_session.status.title()}.')
            time.sleep(30)
        return status
