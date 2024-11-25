from pyVmomi import vim
from transformer import Transformer
import logging

# Initialize Transformer with paths to regex rules
transformer = Transformer("includes/host_site_rules.yml", "includes/host_tenant_rules.yml", "includes/vm_role_rules.yml", "includes/vm_tenant_rules.yml")

def extract_serial_number(other_identifying_info):
    """
    Extracts the serial number from the 'otherIdentifyingInfo' list in host hardware summary.
    Looks for an item with the 'identifierType.key' equal to 'SerialNumberTag'.
    """
    if other_identifying_info:
        for item in other_identifying_info:
            if hasattr(item, "identifierType") and item.identifierType.key == "SerialNumberTag":
                return item.identifierValue
    return None

def fetch_cluster_data(si):
    """
    Fetches cluster information, including cluster name, parent group, and hosts.
    Applies transformations to determine site names.
    """
    logging.info("Fetching clusters from vCenter...")
    content = si.RetrieveContent()
    clusters = []

    for datacenter in content.rootFolder.childEntity:
        for cluster in datacenter.hostFolder.childEntity:
            try:
                logging.info(f"Processing cluster: {cluster.name}")
                # Determine site name from cluster name
                site_name = transformer.host_to_site(cluster.name)
                logging.debug(f"Site name for cluster {cluster.name}: {site_name}")

                # Check if the cluster has hosts
                if hasattr(cluster, "host") and cluster.host:
                    logging.debug(f"Cluster {cluster.name} has {len(cluster.host)} hosts.")
                    hosts = fetch_host_data(cluster.host, site_name)
                else:
                    logging.warning(f"Cluster {cluster.name} has no hosts.")
                    hosts = []

                # Process parent name
                parent_name = cluster.parent.name if cluster.parent else None
                logging.debug(f"Cluster {cluster.name} parent: {parent_name}")

                clusters.append({
                    "name": cluster.name,  # Cluster name
                    "parent_name": parent_name,  # Parent group name
                    "site": site_name,
                    "hosts": hosts,
                })
            except Exception as e:
                logging.error(f"Error processing cluster {cluster.name}: {e}")
    logging.info(f"Fetched {len(clusters)} clusters from vCenter.")
    return clusters


def fetch_host_data(hosts, site_name):
    """
    Fetches host information, applies transformations for cleaning and tenant mapping.
    """
    logging.info(f"Fetching details for {len(hosts)} hosts...")
    host_data = []
    for host in hosts:
        try:
            logging.debug(f"Processing host: {host.name}")
            # Clean hostname and determine tenant
            clean_name = transformer.clean_name(host.name)
            tenant = transformer.host_to_tenant(clean_name)
            logging.debug(f"Transformed host {host.name} -> clean: {clean_name}, tenant: {tenant}")

            host_nics = []
            for vnic in host.config.network.vnic:
                host_nics.append({
                    "type": "vNIC", 
                    "name": vnic.device, 
                    "mac": vnic.spec.mac,
                })
            for pnic in host.config.network.pnic:
                host_nics.append({
                    "type": "pNIC", 
                    "name": pnic.device, 
                    "mac": getattr(pnic, "mac", None),
                })

            serial_number = extract_serial_number(host.summary.hardware.otherIdentifyingInfo)

            host_data.append({
                "name": clean_name,
                "site": site_name,
                "tenant": tenant,
                "nics": host_nics,
                "model": host.hardware.systemInfo.model,
                "vendor": host.hardware.systemInfo.vendor,
                "serial_number": serial_number
            })
        except Exception as e:
            logging.error(f"Error processing host {host.name}: {e}")
    return host_data

def fetch_vm_data(si):
    """
    Fetches VM information, applies transformations for cleaning and tenant mapping.
    """
    logging.info("Fetching VMs from vCenter...")
    content = si.RetrieveContent()
    vms = []
    for datacenter in content.rootFolder.childEntity:
        vm_folder = datacenter.vmFolder
        vms.extend(_fetch_vms_from_folder(vm_folder))
    logging.info(f"Fetched {len(vms)} VMs from vCenter.")
    return vms

def _fetch_vms_from_folder(folder):
    """
    Recursively fetches VMs from a folder and its subfolders, applying transformations.
    """
    vms = []
    for item in folder.childEntity:
        if isinstance(item, vim.VirtualMachine):
            logging.info(f"Processing VM: {item.name}")
            clean_name = transformer.clean_name(item.name)
            tenant = transformer.vm_to_tenant(clean_name)
            role = transformer.vm_to_role(clean_name)

            vm_interfaces = [
                {"name": nic.deviceConfigId, "mac": nic.macAddress, "ip": nic.ipAddress[0]}
                for nic in item.guest.net if nic.ipAddress
            ]
            
            vm_disks = [
                {"label": disk.deviceInfo.label, "capacity": disk.capacityInKB, } 
                for disk in item.config.hardware.device if hasattr(disk, "capacityInKB")
            ]

            vms.append({
                "name": clean_name,  
                "tenant": tenant,  
                'role': role,
                "interfaces": vm_interfaces,  
                "disks": vm_disks,
            })
        elif isinstance(item, vim.Folder):
            # Recursively process subfolders
            vms.extend(_fetch_vms_from_folder(item))
    return vms