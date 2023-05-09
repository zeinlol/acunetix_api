import argparse


def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', help='address [url: http://donki.xyz/ or domain: donki.xyz]', type=str)
    parser.add_argument('-u', '--username', type=str)
    parser.add_argument('-p', '--password', type=str)
    parser.add_argument('-ht', '--host', type=str)
    parser.add_argument('-pt', '--port', type=int)
    parser.add_argument('-o', '--output-file', type=str, default='/wd/report.html')
    parser.add_argument('-s', '--secure', type=bool, default=False)
    parser.add_argument('-px', '--proxy', required=False, type=str)
    return parser.parse_args()


CLI_ARGUMENTS = init_args()
