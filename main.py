import json
import time
from typing import NoReturn
from urllib.parse import urlparse

import report_html_parser
from api.base import AcunetixAPI
from cli_arguments import CLI_ARGUMENTS
from tools import timed_print


def main() -> NoReturn:
    api = AcunetixAPI(
        username=CLI_ARGUMENTS.username,
        password=CLI_ARGUMENTS.password,
        host=CLI_ARGUMENTS.host,
        port=CLI_ARGUMENTS.port,
        secure=CLI_ARGUMENTS.secure
    )
    target_address = CLI_ARGUMENTS.address
    target_proxy = CLI_ARGUMENTS.proxy
    target = api.create_target(address=target_address)
    if target.status_code != 201:
        timed_print(f'Fail to create target for the address: {target_address}.\n'
                    f'Info: {target.text} Status code: {target.status_code}. Content: {target.content}'
                    f'\nExit')
        return
    timed_print(f'The target for the address: {target_address} has been successfully created.')
    target_data = target.json()
    target_id = target_data.get('target_id')
    if target_proxy:
        proxy = urlparse(target_proxy)
        timed_print(f'Set up a proxy configuration with host: {proxy.hostname} and port: {proxy.port}')
        api.setup_proxy_configuration(target_id=target_id, host=proxy.hostname, port=proxy.port,
                                      protocol=proxy.scheme)
    api.run_scan(target_id=target_id)
    scan = api.get_scans()
    # TODO: rework for handling multiple scans
    scan_id = scan.json()['scans'][0].get('scan_id')
    timed_print(f'The scan: {scan_id} was created successfully. Wait for the scan to complete.')
    while True:
        scan = api.get_scan(scan_id=scan_id)
        status = scan.json()['current_session'].get('status')
        scan_status = status.title()
        if status in ['completed', 'failed']:
            timed_print(f'Scanning ended with status: {scan_status}.')
            break
        else:
            timed_print(f'The current scan status is: {scan_status}.')
        time.sleep(30)
    if status == 'completed':
        report_generated = False
        iterations = 0
        while not report_generated:
            iterations += 1
            report = api.get_reports()
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
                report_file = api.download_report(descriptor=report_descriptor)
                with open(CLI_ARGUMENTS.output_file, 'w') as f:
                    f.write(report_file.text)
                report_html_parser.parse(file_absolute_path=CLI_ARGUMENTS.output_file)
            if iterations > 20:
                with open(CLI_ARGUMENTS.output_file, 'w') as f:
                    json.dump({'failed': 'Target scan completed successfully, but report was not generated'}, f)
        timed_print('Exiting...')
        exit(0)
    else:
        with open(CLI_ARGUMENTS.output_file, 'w') as f:
            json.dump({'failed': 'Target scan completed with status: Failed.'}, f, indent=4)


if __name__ == '__main__':
    main()
