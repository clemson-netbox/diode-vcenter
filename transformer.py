import re
import yaml
import logging

class Transformer:
    def __init__(self, host_site_rules_path, host_tenant_rules_path, vm_role_rules_path, vm_tenant_rules_path):
        """
        Initialize the Transformer with paths to regex rules for site and tenant mappings.
        """
        self.host_site_rules = self._load_rules(host_site_rules_path)
        self.host_tenant_rules = self._load_rules(host_tenant_rules_path)
        self.vm_tenant_rules = self._load_rules(vm_tenant_rules_path)
        self.vm_role_rules = self._load_rules(vm_role_rules_path)

    def _load_rules(self, path):
        """
        Load regex rules from a YAML or JSON file.
        """
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"Failed to load rules from {path}: {e}")
            exit(1)

    def apply_regex_replacements(self, value, rules):
        """
        Apply a list of regex replacements to a given value.
        """
        for pattern, replacement in rules:
            if re.match(pattern, value, flags=re.IGNORECASE):
                return re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        return value

    def host_to_site(self, cluster_name):
        """
        Transform a host's cluster name to its site name.
        """
        return self.apply_regex_replacements(cluster_name, self.host_site_rules)

    def host_to_tenant(self, hostname):
        """
        Transform a host's name to its tenant.
        """
        return self.apply_regex_replacements(hostname, self.host_tenant_rules)

    def vm_to_tenant(self, vm_name):
        """
        Transform a VM's name to its tenant.
        """
        return self.apply_regex_replacements(vm_name, self.vm_tenant_rules)
    
    def vm_to_role(self, vm_name):
        """
        Transform a VM's name to its tenant.
        """
        return self.apply_regex_replacements(vm_name, self.vm_role_rules)

    def clean_name(self, name):
        """
        Remove '.clemson.edu.*' from a hostname or VM name.
        """
        return re.sub(r'\.clemson\.edu.*', '', name, flags=re.IGNORECASE)
