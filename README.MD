# Diode vCenter Agent

This Python project is a vCenter to NetBox agent built with the [NetBoxLabs Diode SDK](https://github.com/netboxlabs/diode-sdk-python). It fetches data from vCenter and ingests it into NetBox.

## Features
- Pulls data such as clusters, hosts, NICs, IPs, VMs, interfaces, and disks from vCenter.
- Pushes data to NetBox using the Diode SDK.
- Supports configuration via `.env` files, environment variables, and command-line arguments.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/diode_vcenter_agent.git
   cd diode_vcenter_agent
