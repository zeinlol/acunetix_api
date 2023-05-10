import json
import time
from urllib.parse import urlparse

import report_html_parser
from api.base import AcunetixAPI
from api.classes.scan_status import FINAL_ACUNETIX_STATUSES, AcunetixScanStatuses
from api.classes.target import AcunetixTarget
from core.tools import timed_print


class Analyze:
    def __init__(self, address: str, api: AcunetixAPI, output_file: str, proxy: str | None = None):
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
        self.api.run_scan(target_id=self.target.target_id)
        scan = self.api.get_scans()
        # TODO: rework for handling multiple scans
        scan_id = scan.json()['scans'][0].get('scan_id')
        timed_print(f'The scan: {scan_id} was created successfully. Wait for the scan to complete.')
        while True:
            scan = self.api.get_scan(scan_id=scan_id)
            status = scan.json()['current_session'].get('status')
            scan_status = status.title()
            if status in FINAL_ACUNETIX_STATUSES:
                timed_print(f'Scanning ended with status: {scan_status}.')
                break
            else:
                timed_print(f'The current scan status is: {scan_status}.')
            time.sleep(30)
        if status == AcunetixScanStatuses.COMPLETED.value:
            report_generated = False
            iterations = 0
            while not report_generated:
                iterations += 1
                report = self.api.get_reports()
                json_response = report.json()
                reports = json_response.get('reports', [])
                if not reports:
                    timed_print('No reports. Wait for generation')
                    time.sleep(10)
                    continue
                report_generated = True
                for report in reports:
                    # TODO: Rework. get only connected to scan and target report. parse html to save data in json
                    report_links = report.get('download')
                    report_descriptor = report_links[0].split('/')[-1]
                    report_file = self.api.download_report(descriptor=report_descriptor)
                    with open(self.output_file, 'w') as f:
                        f.write(report_file.text)
                    report_html_parser.parse(file_absolute_path=self.output_file)
                if iterations > 20:
                    with open(self.output_file, 'w') as f:
                        json.dump({'failed': 'Target scan completed successfully, but report was not generated'}, f)
            timed_print('Exiting...')
            exit(0)
        else:
            with open(self.output_file, 'w') as f:
                json.dump({'failed': 'Target scan completed with status: Failed.'}, f, indent=4)
