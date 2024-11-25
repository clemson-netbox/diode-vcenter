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
    Parses command-line arguments and falls back to environment variables.
    """
    parser = argparse.ArgumentParser(description="vCenter to Diode Agent")
    parser.add_argument("--diode-server", default=os.getenv("DIODE_SERVER"), help="Diode server address")
    parser.add_argument("--diode-token", default=os.getenv("DIODE_TOKEN"), help="Diode API token")
    parser.add_argument("--vcenter-host", default=os.getenv("VCENTER_HOST"), help="vCenter host")
    parser.add_argument("--vcenter-user", default=os.getenv("VCENTER_USER"), help="vCenter username")
    parser.add_argument("--vcenter-password", default=os.getenv("VCENTER_PASSWORD"), help="vCenter password")
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
            ingest_with_logging(client, cluster_entities, "clusters")

            # logging.info("Fetching VM data from vCenter...")
            # vm_data = fetch_vm_data(si)
            # logging.info(f"Fetched {len(vm_data)} VMs.")

            # logging.info("Transforming VM data to Diode entities...")
            # vm_entities = prepare_vm_data(vm_data)
            # logging.info(f"Transformed {len(vm_entities)} VM entities.")

            # logging.info("Ingesting VM data into Diode...")
            # ingest_with_logging(client, vm_entities, "VMs")
            # if vm_response.errors:
            #     logging.error(f"VM Errors: {vm_response.errors}")
            # else:
            #     logging.info("VM data ingested successfully.")

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
