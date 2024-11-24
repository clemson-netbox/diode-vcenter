import re
from netboxlabs.diode.sdk.ingester import Device, VirtualMachine, Entity

# Utility function to apply regex transformations
def apply_regex_replacements(value, replacements):
    """
    Applies a series of regex replacement rules to a given value.
    """
    for pattern, replacement in replacements:
        if re.match(pattern, value, flags=re.IGNORECASE):
            return re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    return value

# Regex transformation rules for site
SITE_REPLACEMENTS = [
    (r"(?i)^CU-.+", "Clemson Information Technology Center"),
    (r"(?i)^CUDR-.+|^DR-.+", "University of California San Diego"),
    (r"(?i)^Poole-.+", "Poole Agricultural Center"),
    (r"(?i)^Proto-.+", "Clemson Information Technology Center"),
]

def get_site_name(cluster_name):
    """
    Determines the site name based on the cluster name using regex transformations.
    """
    return apply_regex_replacements(cluster_name, SITE_REPLACEMENTS)

def get_group_name(cluster_parent_name):
    """
    Returns the cluster group name. Currently a direct mapping.
    """
    return cluster_parent_name

def transform_cluster_data(cluster_data):
    """
    Transforms cluster and host data into Diode-compatible entities.
    """
    entities = []

    for cluster in cluster_data:
        site_name = get_site_name(cluster["name"])  # Determine site name
        group_name = get_group_name(cluster["parent_name"])  # Determine group name

        # Process each host in the cluster
        for host in cluster["hosts"]:
            # Prepare NICs as interfaces
            interfaces = [
                {"name": nic["name"], "mac_address": nic["mac"], "type": nic["type"]}
                for nic in host["nics"]
            ]

            # Create Device entity for each host
            device = Device(
                name=host["name"],
                site=site_name,
                cluster_group=group_name,
                device_type=host["model"],
                manufacturer=host["vendor"],
                serial=host["serial_number"],
                role="host",  # Replace with specific role if applicable
                status="active",
                tags=["vCenter", cluster["name"]],
                interfaces=interfaces,  # Host NICs as interfaces
            )
            entities.append(Entity(device=device))

    return entities

def transform_vm_data(vm_data):
    """
    Transforms VM data into Diode-compatible VirtualMachine entities.
    """
    entities = []

    for vm in vm_data:
        # Prepare NICs as interfaces
        interfaces = [
            {"name": nic["name"], "mac_address": nic["mac"], "ip_addresses": [nic["ip"]]}
            for nic in vm["interfaces"]
        ]

        # Prepare disks as storage devices
        disks = [{"name": disk["label"], "capacity": disk["capacity"]} for disk in vm["disks"]]

        # Create VirtualMachine entity for each VM
        virtual_machine = VirtualMachine(
            name=vm["name"],
            cluster=vm.get("cluster"),
            site=vm.get("site"),
            role="application-server",  # Replace with specific VM role if applicable
            status="active",
            tags=["vCenter", vm.get("cluster")],
            interfaces=interfaces,  # VM NICs as interfaces
            disks=disks,  # VM disks directly in the flat structure
        )
        entities.append(Entity(virtual_machine=virtual_machine))

    return entities
