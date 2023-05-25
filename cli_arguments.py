import argparse


def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', type=str, help='address [url: http://donki.xyz/ or domain: donki.xyz]')
    parser.add_argument('-u', '--username', type=str, help='Acunetix user name')
    parser.add_argument('-p', '--password', type=str, help='Acunetix user password')
    parser.add_argument('-ht', '--host', type=str, help='Acunetix API host')
    parser.add_argument('-pt', '--port', type=int, help='Acunetix API port')
    parser.add_argument('-o', '--output-file', type=str, default='report.json', help='Output file')
    parser.add_argument('-s', '--secure', type=bool, default=False, help='Session is secure')
    parser.add_argument('-px', '--proxy', required=False, type=str, help='Proxy settings')
    parser.add_argument('-d', '--demo-mode', type=bool, default=False,
                        help='Handle no licence limitations. Wait for other scans finished')
    return parser.parse_args()


CLI_ARGUMENTS = init_args()
