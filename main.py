import argparse
import os
from dotenv import load_dotenv
from vcenter_connector import connect_to_vcenter, disconnect_vcenter
from diode_connector import connect_to_diode
from data_fetcher import fetch_cluster_data, fetch_vm_data
from data_transformer import transform_and_push_clusters, transform_and_push_vms
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
    si = connect_to_vcenter(args.vcenter_host, args.vcenter_user, args.vcenter_password)

    # Connect to Diode
    diode_client = connect_to_diode(args.diode_server, args.diode_token)

    try:
        # Fetch and push cluster data
        cluster_data = fetch_cluster_data(si)
        transform_and_push_clusters(diode_client, cluster_data)

        # Fetch and push VM data
        vm_data = fetch_vm_data(si)
        transform_and_push_vms(diode_client, vm_data)

    finally:
        # Clean up connections
        disconnect_vcenter(si)


if __name__ == "__main__":
    print(f"Running Diode vCenter Agent version {__version__}")
    main()
