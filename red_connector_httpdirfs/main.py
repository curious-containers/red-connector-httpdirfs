from cc_connector_cli.connector_cli import run_connector
from red_connector_httpdirfs.httpdirfs import HttpDirFs
from red_connector_httpdirfs.version import VERSION


def main():
    run_connector(HttpDirFs, version=VERSION)


if __name__ == '__main__':
    main()
