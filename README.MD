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
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install the package:
   ```bash
   python setup.py install
   ```

## Usage
1. Configure `.env` file:
   ```plaintext
   DIODE_SERVER=diode.example.com
   DIODE_TOKEN=your_diode_api_token
   VCENTER_HOST=vcenter.example.com
   VCENTER_USER=administrator@vsphere.local
   VCENTER_PASSWORD=your_vcenter_password
   ```

2. Run the agent:
   ```bash
   python main.py
   ```

3. Or use command-line arguments:
   ```bash
   python main.py --diode-server diode.local --diode-token abc123 \
       --vcenter-host vcenter.local --vcenter-user admin --vcenter-password password
   ```

## License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
