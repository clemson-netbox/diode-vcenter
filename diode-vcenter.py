#!/usr/bin/env python3

import argparse
import os
from dotenv import load_dotenv
from diode_connector import connect_to_diode
from vcenter_connector import connect_to_vcenter, disconnect_vcenter
from data_fetcher import fetch_cluster_data, fetch_vm_data
from data_transformer import transform_cluster_data, transform_vm_data
from version import __version__

# Load .env file
load_dotenv()

def parse_arguments():
    parser = argparse.ArgumentParser(description="vCenter to Diode Agent")
    parser.add_argument("--diode-server", default=os.getenv("DIODE_SERVER"), help="Diode server address")
    parser.add_argument("--diode-token", default=os.getenv("DIODE_TOKEN"), help="Diode API token")
    parser.add_argument("--vcenter-host", default=os.getenv("VCENTER_HOST"), help="vCenter host")
    parser.add_argument("--vcenter-user", default=os.getenv("VCENTER_USER"), help="vCenter username")
    parser.add_argument("--vcenter-password", default=os.getenv("VCENTER_PASSWORD"), help="vCenter password")
    return parser.parse_args()


def main():
    # Parse arguments
    args = parse_arguments()

    # Connect to vCenter
    si = connect_to_vcenter()

    # Connect to Diode
    with connect_to_diode() as client:
        try:
            # Fetch cluster and VM data from vCenter
            cluster_data = fetch_cluster_data(si)
            vm_data = fetch_vm_data(si)

            # Transform data into Diode-compatible entities
            cluster_entities = transform_cluster_data(cluster_data)
            vm_entities = transform_vm_data(vm_data)

            # Ingest cluster data
            cluster_response = client.ingest(entities=cluster_entities)
            if cluster_response.errors:
                print(f"Cluster Errors: {cluster_response.errors}")

            # Ingest VM data
            vm_response = client.ingest(entities=vm_entities)
            if vm_response.errors:
                print(f"VM Errors: {vm_response.errors}")

        finally:
            # Disconnect from vCenter
            disconnect_vcenter(si)



if __name__ == "__main__":
    print(f"Running Diode vCenter Agent version {__version__}")
    main()


