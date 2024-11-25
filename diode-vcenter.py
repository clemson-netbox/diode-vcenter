#!/usr/bin/env python3

import argparse
import os
import logging
from dotenv import load_dotenv
from netboxlabs.diode.sdk import DiodeClient
from vcenter_connector import connect_to_vcenter, disconnect_vcenter
from vcenter_fetcher import fetch_cluster_data, fetch_vm_data
from data_conversion import prepare_cluster_data, prepare_vm_data
from version import __version__

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # Change to logging.DEBUG for more verbosity
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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
        "--VCENTER-host",
        default=os.getenv("VCENTER_HOST"),
        required=not os.getenv("VCENTER_HOST"),
        help="Catalyst Center host (or set via VCENTER_HOST environment variable)"
    )
    parser.add_argument(
        "--VCENTER-user",
        default=os.getenv("VCENTER_USER"),
        required=not os.getenv("VCENTER_USER"),
        help="Catalyst Center username (or set via VCENTER_USER environment variable)"
    )
    parser.add_argument(
        "--VCENTER-password",
        default=os.getenv("VCENTER_PASSWORD"),
        required=not os.getenv("VCENTER_PASSWORD"),
        help="Catalyst Center password (or set via VCENTER_PASSWORD environment variable)"
    )
    parser.add_argument(
        "--VCENTER-verify",
        default=os.getenv("VCENTER_VERIFY", "true").lower() in ("true", "1", "yes"),
        type=lambda x: x.lower() in ("true", "1", "yes"),
        help="Verify Catalyst Center SSL certificate (default: true, or set via VCENTER_VERIFY environment variable)"
    )

    return parser.parse_args()


def ingest_with_logging(client, entities, entity_type):
    try:
        response = client.ingest(entities=entities)
        if response.errors:
            logging.error(f"Diode Ingestion Errors for {entity_type}: {response.errors}")
        else:
            logging.info(f"Successfully ingested {len(entities)} {entity_type}.")
    except Exception as e:
        logging.error(f"Error during {entity_type} ingestion: {e}")

def main():
    # Parse arguments
    args = parse_arguments()

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
            cluster_data = fetch_cluster_data(si)
            logging.info(f"Fetched {len(cluster_data)} clusters.")

            logging.info("Transforming cluster data to Diode entities...")
            cluster_entities = prepare_cluster_data(cluster_data)
            logging.info(f"Transformed {len(cluster_entities)} cluster entities.")

            logging.info("Ingesting cluster data into Diode...")
            logging.debug(f"Cluster entities being sent: {cluster_entities}")
            ingest_with_logging(client, cluster_entities, "clusters")

            logging.info("Fetching VM data from vCenter...")
            vm_data = fetch_vm_data(si)
            logging.info(f"Fetched {len(vm_data)} VMs.")

            logging.info("Transforming VM data to Diode entities...")
            vm_entities = prepare_vm_data(vm_data)
            logging.info(f"Transformed {len(vm_entities)} VM entities.")

            logging.info("Ingesting VM data into Diode...")
            logging.debug(f"VM entities being sent: {vm_entities}")
            ingest_with_logging(client, vm_entities, "VMs")
            
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
