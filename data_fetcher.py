def fetch_cluster_data(si):
    """
    Fetches cluster information, including cluster name, parent group, and hosts.
    """
    content = si.RetrieveContent()
    clusters = []
    for datacenter in content.rootFolder.childEntity:
        for cluster in datacenter.hostFolder.childEntity:
            clusters.append({
                "name": cluster.name,  # Cluster name
                "parent_name": cluster.parent.name if cluster.parent else None,  # Parent group name
                "hosts": fetch_host_data(cluster.host),  # List of hosts in this cluster
            })
    return clusters

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


def fetch_host_data(hosts):
    """
    Fetches host information, including name, CPU, memory, NICs (vNICs and pNICs), 
    and hardware details like serial number, model, and vendor.
    """
    host_data = []
    for host in hosts:
        host_nics = []

        # Collect vNICs
        for vnic in host.config.network.vnic:
            host_nics.append({
                "type": "vNIC",  # Virtual NIC
                "name": vnic.device,
                "mac": vnic.spec.mac,
                "ip": vnic.spec.ip.ipAddress if vnic.spec.ip else None,
            })

        # Collect pNICs (physical NICs)
        for pnic in host.config.network.pnic:
            host_nics.append({
                "type": "pNIC",  # Physical NIC
                "name": pnic.device,
                "mac": pnic.mac if hasattr(pnic, "mac") else None,
                "link_speed": pnic.linkSpeed.speedMb if pnic.linkSpeed else None,  # Link speed in Mbps
            })

        # Extract serial number
        serial_number = extract_serial_number(host.summary.hardware.otherIdentifyingInfo)

        # Append host details
        host_data.append({
            "name": host.name,  # Host name
            "cpus": host.hardware.cpuInfo.numCpuCores,  # Number of CPUs
            "memory": host.hardware.memorySize,  # Memory size in bytes
            "nics": host_nics,  # Combined vNIC and pNIC details
            "serial_number": serial_number,  # Extracted serial number
            "model": host.hardware.systemInfo.model,  # Hardware model
            "vendor": host.hardware.systemInfo.vendor,  # Hardware vendor
        })
    return host_data


def fetch_vm_data(si):
    """
    Fetches VM information, including name, cluster, interfaces, IPs, and disks.
    """
    content = si.RetrieveContent()
    vms = []
    for datacenter in content.rootFolder.childEntity:
        for vm in datacenter.vmFolder.childEntity:
            vm_interfaces = []
            vm_disks = []

            # Get VM NICs and IPs
            for nic in vm.guest.net:
                vm_interfaces.append({
                    "name": nic.deviceConfigId,  # Interface name
                    "mac": nic.macAddress,  # MAC address
                    "ip": nic.ipAddress[0] if nic.ipAddress else None,  # Primary IP
                })

            # Get VM Disks
            for disk in vm.config.hardware.device:
                if hasattr(disk, "capacityInKB"):
                    vm_disks.append({
                        "label": disk.deviceInfo.label,
                        "capacity": disk.capacityInKB,  # Capacity in KB
                    })

            # Append VM data
            vms.append({
                "name": vm.name,  # VM name
                "cluster": vm.runtime.host.parent.name if vm.runtime.host else None,  # Parent cluster name
                "interfaces": vm_interfaces,  # List of NICs
                "disks": vm_disks,  # List of disks
            })
    return vms
