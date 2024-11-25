from pyVmomi import vim
from transformer import Transformer
import logging

# Initialize Transformer with paths to regex rules
transformer = Transformer("includes/host_site_rules.yml", "includes/host_tenant_rules.yml", "includes/vm_role_rules.yml", "includes/vm_tenant_rules.yml")

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
            logging.info(f"Processing cluster: {cluster.name}")
            # Determine site name from cluster name
            site_name = transformer.host_to_site(cluster.name)
            # Check if the cluster has hosts
            if hasattr(cluster, "host") and cluster.host:
                hosts = fetch_host_data(cluster.host, site_name)  # List of hosts in this cluster
            else:
                logging.warning(f"Cluster {cluster.name} has no hosts.")
                hosts = []

            clusters.append({
                "name": cluster.name,  # Cluster name
                "parent_name": cluster.parent.name if cluster.parent else None,  # Parent group name
                "site": site_name,
                "hosts": hosts,
            })
    logging.info(f"Fetched {len(clusters)} clusters from vCenter.")
    return clusters

def fetch_host_data(hosts, site_name):
    """
    Fetches host information, applies transformations for cleaning and tenant mapping.
    """
    logging.info(f"Fetching details for {len(hosts)} hosts...")
    host_data = []
    for host in hosts:
        logging.info(f"Processing host: {host.name}")
        # Clean hostname and determine tenant
        clean_name = transformer.clean_name(host.name)
        tenant = transformer.host_to_tenant(clean_name)
        host_nics = []

        # Collect vNICs and pNICs
        for vnic in host.config.network.vnic:
            host_nics.append({"type": "vNIC", "name": vnic.device, "mac": vnic.spec.mac})
        for pnic in host.config.network.pnic:
            host_nics.append({"type": "pNIC", "name": pnic.device, "mac": getattr(pnic, "mac", None)})

        # Append host details
        host_data.append({
            "name": clean_name,  # Cleaned host name
            "site": site_name,  # Site determined from cluster name
            "tenant": tenant,  # Tenant determined from hostname
            "nics": host_nics,  # NIC details
            "model": host.hardware.systemInfo.model,
            "vendor": host.hardware.systemInfo.vendor,
        })
    logging.info(f"Fetched details for {len(host_data)} hosts.")
    return host_data

def fetch_vm_data(si):
    """
    Fetches VM information, applies transformations for cleaning and tenant mapping.
    """
    logging.info("Fetching VMs from vCenter...")
    content = si.RetrieveContent()
    vms = []
    for datacenter in content.rootFolder.childEntity:
        vm_folder = datacenter.vmFolder  # Entry point to VMs
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
            role = transformer.vm_tol_role(clean_name)

            vm_interfaces = [
                {"name": nic.deviceConfigId, "mac": nic.macAddress, "ip": nic.ipAddress[0]}
                for nic in item.guest.net if nic.ipAddress
            ]

            vms.append({
                "name": clean_name,  # Cleaned VM name
                "tenant": tenant,  # Tenant determined from VM name
                'role': role,
                "interfaces": vm_interfaces,  # NIC details
            })
        elif isinstance(item, vim.Folder):
            # Recursively process subfolders
            vms.extend(_fetch_vms_from_folder(item))
    return vms
