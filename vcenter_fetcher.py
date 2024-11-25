from pyVmomi import vim
from transformer import Transformer
import logging

# Initialize Transformer with paths to regex rules
transformer = Transformer("includes/host_site_rules.yml", "includes/host_tenant_rules.yml", "includes/vm_role_rules.yml", "includes/vm_tenant_rules.yml", "includes/skip_vms.yml")

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
                tenant = transformer.host_to_tenant(cluster.name)
                logging.debug(f"Tenant name for cluster {cluster.name}: {tenant}")
                # Check if the cluster has hosts
                if hasattr(cluster, "host") and cluster.host:
                    logging.debug(f"Cluster {cluster.name} has {len(cluster.host)} hosts.")
                    hosts = fetch_host_data(cluster.host, site_name)
                else:
                    logging.warning(f"Cluster {cluster.name} has no hosts.")
                    hosts = []

                # Process parent name
                parent_name = cluster.parent.parent.name if cluster.parent.parent else None
                logging.debug(f"Cluster {cluster.name} parent: {parent_name}")

                clusters.append({
                    "name": cluster.name,
                    "group": parent_name, 
                    "site": site_name,
                    "hosts": hosts,
                    "tenant": tenant,
                })
            except Exception as e:
                logging.error(f"Error processing cluster {cluster.name}: {e}")
    logging.info(f"Fetched {len(clusters)} clusters from vCenter.")
    return clusters

def get_nic_type(link_speed):
    """
    Maps link speed in Mbps to NIC type based on predefined replacements.
    """
    if link_speed is None:
        return "other"
    
    link_speed_map = {
        1000: "1000base-t",
        10000: "10gbase-x-sfpp",
        25000: "25gbase-x-sfp28",
        40000: "40gbase-x-qsfpp",
        100000: "100gbase-x-qsfp28",
    }
    return link_speed_map.get(link_speed, "other")

def get_cidr(ip, subnet_mask):
    """
    Converts an IP address and subnet mask to CIDR notation (x.x.x.x/y).
    """
    from ipaddress import ip_network
    try:
        # Convert subnet mask to prefix length
        network = ip_network(f"{ip}/{subnet_mask}", strict=False)
        return str(network)
    except Exception as e:
        logging.error(f"Failed to convert {ip} and {subnet_mask} to CIDR: {e}")
        return None
    
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

            # Process vNICs (Virtual NICs)
            for vnic in host.config.network.vnic:
                ip_addresses = []
                if vnic.spec.ip and hasattr(vnic.spec.ip, 'ipAddress'):
                    for ip in vnic.spec.ip.ipAddress.split(','):
                        subnet_mask = vnic.spec.ip.subnetMask if hasattr(vnic.spec.ip, 'subnetMask') else None
                        if subnet_mask:
                            cidr = get_cidr(ip, subnet_mask)
                            if cidr:
                                ip_addresses.append(cidr)
                        else:
                            ip_addresses.append(ip)  # Add raw IP if no subnet mask

                nic_data = {
                    "type": "virtual",
                    "name": vnic.device,
                    "mac": vnic.spec.mac,
                    "ip_addresses": vnic.spec.ip.ipAddress.split(',') if vnic.spec.ip and hasattr(vnic.spec.ip, 'ipAddress') else [],
                    "dvs_name": vnic.distributedVirtualPort.switchUuid if hasattr(vnic, "distributedVirtualPort") else None,
                    "portgroup_name": vnic.portgroup if hasattr(vnic, "portgroup") else None,
                }
                host_nics.append(nic_data)

            # Process pNICs (Physical NICs)
            for pnic in host.config.network.pnic:
                link_speed = pnic.linkSpeed.speedMb if pnic.linkSpeed else None
                nic_type = get_nic_type(link_speed)

                nic_data = {
                    "type": nic_type,
                    "name": pnic.device,
                    "mac": getattr(pnic, "mac", None),
                    "link_speed": link_speed,
                    "ip_addresses": [],  
                    "dvs_name": None,
                    "portgroup_name": None,
                }
                host_nics.append(nic_data)

            serial_number = extract_serial_number(host.summary.hardware.otherIdentifyingInfo)

            host_data.append({
                "name": clean_name,
                "site": site_name,
                "cluster": host.parent.name,
                "tenant": tenant,
                "nics": host_nics,
                "model": host.hardware.systemInfo.model,
                "vendor": host.hardware.systemInfo.vendor,
                "serial_number": serial_number,
                "tags": ["Diode-vCenter-Agent"],  # Tags for grouping in Diode

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
    for vm in folder.childEntity:
        if isinstance(vm, vim.VirtualMachine):
            logging.info(f"Processing VM: {vm.name}")
            clean_name = transformer.clean_name(vm.name)
            skip = transformer.should_skip_vm(vm.name)
            
            if skip:
                continue  # Skip this VM
                
            vm_interfaces = [
                {"name": nic.deviceInfo.label, "mac": nic.macAddress, "ip": nic.ipAddress[0], "enabled": nic.connectable.connected if hasattr(nic, 'connectable') else False,}
                for nic in vm.guest.net if nic.ipAddress
            ]
            
            vm_disks = [
                {"label": disk.deviceInfo.label, "capacity": disk.capacityInKB, } 
                for disk in vm.config.hardware.device if hasattr(disk, "capacityInKB")
            ]

            # "datastore": device.backing.datastore.name if hasattr(device.backing, 'datastore') else "",
            # "disk_type": device.backing.diskMode if hasattr(device.backing, 'diskMode') else "",
            # "thin_thick": "Thin Provisioned" if hasattr(device.backing, 'thinProvisioned') else "Thick Provisioned",
            # "vmdk": device.backing.fileName if hasattr(device.backing, 'fileName') else "",
            
            vms = {
                    "name": vm.name,
                    "status": "active" if vm.runtime.powerState == "poweredOn" else "offline",
                    "site": transformer.host_to_site(vm.runtime.host.name) if vm.runtime.host else None,
                    "cluster": vm.runtime.host.parent.name if vm.runtime.host else None,
                    "role": transformer.vm_to_role(vm.name),  # Custom logic to map VM names to roles
                    "device": clean_name(vm.runtime.host.name),  # Host name without domain
                    "platform": vm.guest.guestFullName if vm.guest and vm.guest.guestFullName else "Unknown",
                    "vcpus": vm.config.hardware.numCPU if hasattr(vm.config.hardware, "numCPU") else None,
                    "memory": vm.config.hardware.memoryMB if hasattr(vm.config.hardware, "memoryMB") else None,
                    "description": vm.summary.config.annotation if vm.summary.config.annotation else None,
                    "comments": None,  # Placeholder for any comments
                    "tags": ["Diode-vCenter-Agent"],  # Tags for grouping in Diode
                    "interfaces": vm_interfaces,  # List of NICs
                    "disks": vm_disks,  # List of disks
                }
            
        elif isinstance(vm, vim.Folder):
            # Recursively process subfolders
            vms.extend(_fetch_vms_from_folder(vm))
    return vms
