#!/usr/bin/env python3

import argparse
import os
import logging
from dotenv import load_dotenv
from netboxlabs.diode.sdk import DiodeClient
from vcenter_connector import connect_to_vcenter, disconnect_vcenter
from vcenter_fetcher import fetch_cluster_data, fetch_vm_data
from data_conversion import prepare_data
from version import __version__

# Load .env file
load_dotenv()

def parse_arguments():
    """
    Parse command-line arguments with environment variable defaults,
    making all arguments effectively required.
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Catalyst Center to Diode Agent")

    parser.add_argument(
        "--diode-server",
        default=os.getenv("DIODE_SERVER"),
        required=not os.getenv("DIODE_SERVER"),
        help="Diode server address (or set via DIODE_SERVER environment variable)"
    )
    parser.add_argument(
        "--diode-api-key",
        default=os.getenv("DIODE_API_KEY"),
        required=not os.getenv("DIODE_API_KEY"),
        help="Diode API token (or set via DIODE_API_KEY environment variable)"
    )
    parser.add_argument(
        "--vcenter-host",
        default=os.getenv("VCENTER_HOST"),
        required=not os.getenv("VCENTER_HOST"),
        help="Catalyst Center host (or set via VCENTER_HOST environment variable)"
    )
    parser.add_argument(
        "--vcenter-user",
        default=os.getenv("VCENTER_USER"),
        required=not os.getenv("VCENTER_USER"),
        help="Catalyst Center username (or set via VCENTER_USER environment variable)"
    )
    parser.add_argument(
        "--vcenter-password",
        default=os.getenv("VCENTER_PASSWORD"),
        required=not os.getenv("VCENTER_PASSWORD"),
        help="Catalyst Center password (or set via VCENTER_PASSWORD environment variable)"
    )
    parser.add_argument(
        "--vcenter-verify",
        default=os.getenv("VCENTER_VERIFY", "true").lower() in ("true", "1", "yes"),
        type=lambda x: x.lower() in ("true", "1", "yes"),
        help="Verify Catalyst Center SSL certificate (default: true, or set via VCENTER_VERIFY environment variable)"
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging Level INFO, WARNING, ERROR, DEBUG"
    )
    return parser.parse_args()


def main():
    # Parse arguments
    args = parse_arguments()
    # Configure logging
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logging.info("Starting Diode vCenter Agent...")

    # Connect to vCenter
    si = connect_to_vcenter(args.vcenter_host, args.vcenter_user, args.vcenter_password)
    if not si:
        logging.error("Failed to connect to vCenter. Exiting.")
        return

    # Connect to Diode
    with DiodeClient(
        target=f"grpc://{args.diode_server}/diode",
        app_name="diode-vcenter",
        app_version=__version__,
    ) as client:
        try:
            logging.info("Fetching cluster data from vCenter...")
            cluster_data = fetch_cluster_data(si,logging)
            logging.info(f"Fetched {len(cluster_data)} clusters.")

            logging.info("Fetching VM data from vCenter...")
            #vm_data = fetch_vm_data(si,logging)
            logging.info(f"Fetched {len(vm_data)} VMs.")
            vm_data = {}
            logging.info("Transforming data to Diode entities...")
            prepare_data(client,cluster_data,vm_data,logging)
            
            
        except Exception as e:
            logging.error(f"An error occurred during the process: {e}")
        finally:
            # Disconnect from vCenter
            logging.info("Disconnecting from vCenter...")
            disconnect_vcenter(si)
            logging.info("Disconnected from vCenter.")


if __name__ == "__main__":
    logging.info(f"Running Diode vCenter Agent version {__version__}")
    main()
