def fetch_cluster_data(si):
    content = si.RetrieveContent()
    clusters = []
    for datacenter in content.rootFolder.childEntity:
        for cluster in datacenter.hostFolder.childEntity:
            clusters.append({
                "name": cluster.name,
                "hosts": fetch_host_data(cluster.host)
            })
    return clusters

def fetch_host_data(hosts):
    host_data = []
    for host in hosts:
        host_nics = [{"name": nic.device, "mac": nic.mac} for nic in host.config.network.vnic]
        host_data.append({
            "name": host.name,
            "cpus": host.hardware.cpuInfo.numCpuCores,
            "memory": host.hardware.memorySize,
            "nics": host_nics
        })
    return host_data

def fetch_vm_data(si):
    content = si.RetrieveContent()
    vms = []
    for datacenter in content.rootFolder.childEntity:
        for vm in datacenter.vmFolder.childEntity:
            vm_interfaces = [{"name": nic.deviceInfo.label, "mac": nic.macAddress} for nic in vm.config.hardware.device if hasattr(nic, 'macAddress')]
            vm_disks = [{"label": disk.deviceInfo.label, "capacity": disk.capacityInKB} for disk in vm.config.hardware.device if hasattr(disk, 'capacityInKB')]
            vms.append({
                "name": vm.name,
                "interfaces": vm_interfaces,
                "disks": vm_disks
            })
    return vms
