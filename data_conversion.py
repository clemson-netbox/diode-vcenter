import re
from netboxlabs.diode.sdk.ingester import Device, VirtualMachine, Cluster, Interface, VMInterface, VirtualDisk, Entity


def prepare_cluster_data(cluster_data):
    """
    Transforms cluster and host data into Diode-compatible entities.
    """
    entities = []

    for cluster in cluster_data:
        cluster_entity = Cluster(
            name=cluster['name'],
            group=cluster['group'],
            site=cluster['site'],
            status='active',
            tags=["Diode"],
        )
        entities.append(Entity(cluster=cluster_entity))
                    
        for host in cluster["hosts"]:
           
            # Create Device entity for each host
            device_data = Device(
                name=host["name"],
                site=cluster["site"],
                device_type=host["model"],
                manufacturer=host["vendor"],
                serial=host["serial_number"],
                role="Hypervisor Host",  # Replace with specific role if applicable
                status="active",
                tags=["Diode"],
                #interfaces=interfaces,  # Host NICs as interfaces
            )
            entities.append(Entity(device=device_data))
            
            for nic in host["nics"]:
                interface_data = Interface(
                    name=nic["name"], 
                    device=device_data,  
                    mac_address=nic["mac"],
                    type=nic["type"],
                )       
                entities.append(Entity(interface=interface_data))

    return entities

def prepare_vm_data(vm_data):
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
            cluster=vm["cluster"],
            site=vm["site"],
            role=vm['role'],
            status="active",
            tags=["Diode"],
            #interfaces=interfaces,  # VM NICs as interfaces
            #disks=disks,  # VM disks directly in the flat structure
        )
        entities.append(Entity(virtual_machine=virtual_machine))

    return entities
