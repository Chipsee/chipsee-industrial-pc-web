from lib.chipsee_board import board
import ipaddress
import subprocess

class IpConfig(object):
    """
    Set static IP from user input form.
    There are several tools an OS can use to manage network settings, e.g: dhcpcd.service, NetworkManager.
    Different Chipsee industrial PCs might use different tools, here are two examples:
    - Raspberry Pi Based
        Raspberry Pi based system (CM4) uses dhcpcd(dhcpcd.service) to control network.
        It reads/writes to /etc/dhcpcd.conf file to control static IP of a nic.
    - PX30(Debian)
        PX30 (Debian10 Buster) uses NetworkManager(network-manager.service) to control network.
        nmcli is a convenient command line tool to manage network configurations for NetworkManager based Linux system.
    
    Properties:
    - nic: String. The name of network interface card, like: "eth0", "wlan0".
    - ip_version: String. One of "ipv4" and "ipv6".
    """
    SUPPORTED_NETTOOLS = ['dhcpcd', 'NetworkManager']
    def __init__(self):
        self.nics = board.devices().get("nics") or {}
        self.new_configs = {}
        self.nic = None
        self.ip_version = None
        self.form_errors = []
        self.linux_nettool = None
    
    def handle_form(self, form):
        self.validate_form(form)
        self.validate_nettool()
        self.check_connectivity()
        if self.form_errors:
            return { 
                    "msg": "{} error(s) prohibited IP from being set, please check the error messages below:".format(len(self.form_errors)), 
                    "errors": self.form_errors
                    }
        else:
            self.update_config()
            return { 
                    "msg": "Updated IP settings for {}.".format(self.nic), 
                    "errors": self.form_errors 
                    }

    def validate_form(self, form):
        """
        Validate user input form from HTML. 
        Some settings should be valid IP format that will be stored in the dhcpcd.conf file later.
        """
        self.validate_version(form)
        self.validate_address(form)
        self.validate_gateway_and_dns(form)
        self.validate_dns_search(form)
        self.validate_nic(form)
    
    def update_config(self):
        """
        Methods to update network config(set static IP or set to auto):
        - dhcpcd:
            Mostly read/write a dhcpcd.conf file.
            Redundent settings will be removed, new settings will be appended to the end of this file.
        - NetworkManager:
            Mostly to build a nmcli command to be invoked in command line with subprocess.run().
        """
        if self.linux_nettool == "dhcpcd":
            self.dhcpcd_conf_path = '/etc/dhcpcd.conf'
            self.load_current_dhcpcd_conf()
            self.remove_nic_settings_from_dhcpcd_conf()
            self.append_new_settings_to_dhcpcd_conf()
            self.restart_net_service()
        elif self.linux_nettool == "NetworkManager":
            self.modify_nmcli_conn()
            self.restart_net_service()
            
    def run_nmcli_cmd(self, cmd):
        try:
            r = subprocess.run(cmd, capture_output=True, check=True)
            return 0, r.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            rc = e.returncode
            stderr = e.stderr.decode('utf-8')
            print(stderr)
            return rc, stderr

    def check_connectivity(self):
        if self.linux_nettool == "dhcpcd":
            return
        elif self.linux_nettool == "NetworkManager":
            self.check_nmcli_connectivity()
        
    def check_nmcli_connectivity(self):
        """
        Use nmcli terse command to show existing active connections.
        e.g.: 
        [
            'Ethernet connection 1:6d8127e5-e31e-44b1-a868-d5e798547ed2:802-3-ethernet:eth0', 
            'basement wifi:ddda71a4-4cb0-4ac1-866a-1fa0c0948033:802-11-wireless:wlan0'
        ]
        """
        err_code, out = self.run_nmcli_cmd(["nmcli", "-t", "con", "show", "--active"])
        if err_code != 0:
            self.form_errors.append("Cannot find an active connection for {}, please check network connectivity first.".format(self.nic))
            return
        existing_connections = out.strip().split('\n')
        for conn in existing_connections:
            if self.nic in conn:
                # e.g.: eth0 should be the last 4 char of 'Ethernet connection 1:6d...e2:802-3-ethernet:eth0'
                self.nmcli_conn = conn
                return
        # If no active connection is found for this nic.
        self.form_errors.append("Cannot find an active connection for {}, please check network connectivity first.".format(self.nic))
            
    def modify_nmcli_conn(self):
        """
        nmcli conn info, e.g.:  'Ethernet connection 1:6d8127e5-e31e-44b1-a868-d5e798547ed2:802-3-ethernet:eth0'
                                'basement wifi:ddda71a4-4cb0-4ac1-866a-1fa0c0948033:802-11-wireless:wlan0'
        """
        if not self.nmcli_conn:
            return
        self.nmcli_conn_name = self.nmcli_conn.split(':')[0]
        
        cmd = ["sudo", "nmcli", "con", "mod", self.nmcli_conn_name]
        if not self.new_configs:
            # All fields are set empty, will set this IPv4/v6 version's config to auto.
            cmd += ["{}.method".format(self.ip_version), "auto"]
            err_code, stdout = self.run_nmcli_cmd(cmd)
            if err_code != 0:
                self.form_errors.append("nmcli error: {}.".format(stdout))
            return
        else:
            cmd += ["{}.method".format(self.ip_version), "manual"]
        addr = self.new_configs.get('address', '')
        cmd += ["{}.address".format(self.ip_version), addr]
            
        gateway = self.new_configs.get('gateway', '')
        cmd += ["{}.gateway".format(self.ip_version), gateway]
        
        dns = "{} {}".format(self.new_configs.get('dns-server', ''), self.new_configs.get('dns-server-secondary', '')).strip()
        cmd += ["{}.dns".format(self.ip_version), dns]
        
        dns_search = self.new_configs.get('dns-search', '')
        cmd += ["{}.dns-search".format(self.ip_version), dns_search]
        
        err_code, stdout = self.run_nmcli_cmd(cmd)
        if err_code != 0:
            self.form_errors.append("nmcli error: {}.".format(stdout))
            
    def validate_dns_search(self, form):
        if form['dns-search']:
            self.new_configs['dns-search'] = form['dns-search']
    
    def validate_version(self, form):
        version = form.get('ip-version')
        if not version:
            self.form_errors.append("Please select a IP version.")
            return
        if version in ['ipv4', 'ipv6']:
            self.ip_version = version
        else:
            self.form_errors.append("{} is not a valid IP version, available versions are: ipv4 and ipv6".format(version))

    def validate_nic(self, form):
        """
        User input nic field(usually with a radio button or dropdown menu) should have the same name as Linux nic.
        Different Linux might use different net tools to manage nic, such as dhcpcd or NetworkManager.
        """
        nic = form.get('nic')
        if not nic:
            self.form_errors.append("Please select a network interface.")
            return
        if nic in self.nics:
            self.nic = nic
        else:
            avai_nics = " ".join(list(self.nics.keys()))
            nic_error_msg = "'{}' is not a valid network interface card of this PC, available nics are: {}.".format(nic, avai_nics)
            self.form_errors.append(nic_error_msg)
            return
        
    def validate_nettool(self):
        # Ensure the correspoding net tool of this nic is supported.
        if not self.nic:
            return
        self.linux_nettool = self.nics.get(self.nic)
        if self.linux_nettool in self.SUPPORTED_NETTOOLS:
            return
        else:
            nettool_error_msg = "The specified Linux network tool: {} isn't supported. Currently supports: {}.".format(self.linux_nettool, ", ".join(self.SUPPORTED_NETTOOLS))
            self.form_errors.append(nettool_error_msg)
            
    def validate_address(self, form):
        if not form['address']:
            return
        try:
            if self.ip_version == "ipv4":
                self.new_configs["address"] = str(ipaddress.IPv4Interface(form["address"]))
            elif self.ip_version == "ipv6":
                self.new_configs["address"] = str(ipaddress.IPv6Interface(form["address"]))
        except ipaddress.AddressValueError as e:
            self.form_errors.append("Address field: {}".format(e))
            return 
        except ipaddress.NetmaskValueError as e:
            self.form_errors.append("Address field: {}".format(e))
            return 
        
    def validate_gateway_and_dns(self, form):
        """
        'gateway', 'dns-server' and 'dns-server-secondary' should be of type IPv4Address/IPv6Address.
        If they're not in the correct format, user might have input a wrong IP, 
        This method adds the invalid field to error message to inform the user.
        """
        fields = {
            'gateway': 'Gateway',
            'dns-server': 'Primary DNS server',
            'dns-server-secondary': 'Secondary DNS server',
        }
        for field in fields:
            if not form[field]:
                continue
            try:
                if self.ip_version == "ipv4":
                    self.new_configs[field] = str(ipaddress.IPv4Address(form[field]))
                elif self.ip_version == "ipv6":
                    self.new_configs[field] = str(ipaddress.IPv6Address(form[field]))
            except ipaddress.AddressValueError as e:
                self.form_errors.append("{} field: {}".format(fields[field], e))
                  
    def load_current_dhcpcd_conf(self):
        with open(self.dhcpcd_conf_path, 'r') as f:
            self.dhcpcd_conf = f.readlines()
            
    def remove_nic_settings_from_dhcpcd_conf(self):
        """
        Remove the settings of a nic from `dhcpcd.conf` file,
        then return the remaining settings.
        E.g:
        From /etc/dhcpcd.conf remove settings of eth0:
            abc
            interface eth0
            static ip_address=192.168.0.1
            defg
        will return:
            [
                "abc\n",
                "defg\n"
            ]
        """
        res = []
        found_nic = False
        for (i, line) in enumerate(self.dhcpcd_conf):
            if line.strip() == "interface {}".format(self.nic):
                found_nic = True
                continue
            if found_nic == True:
                print(line)
                # The lines right after finding an "interface {nic}" should be the settings of this nic.
                found_keyword = False
                for keyword in ['routers=', 'domain_name_servers=', 'noipv6', 'ip_address=', 'domain_search=', 'ip6_address=', 'domain_search=']:
                    if keyword in line:
                        found_keyword = True
                        break
                if found_keyword:
                    # Need to leave out the line which includes these keywords, because they're the settings of this nic.
                    continue
                else:
                    # After the settings of this nic, the following lines should be other configs (or EOF) of this dhcpcd.conf file.
                    # And this line should be reserved, as well as the following lines.
                    res.append(line)
                    found_nic = False
            else:
                found_nic = False
                res.append(line)
                continue
        self.dhcpcd_conf = res
    
    def append_new_settings_to_dhcpcd_conf(self):
        """
        Append nic specific settings (if any) to the /etc/dhcpcd.conf configuration file.
        Then dhcpcd.service will pick up this file for further configuration later.
        """
        with open(self.dhcpcd_conf_path, 'w') as f:
            for line in self.dhcpcd_conf:
                f.write(line)
            if not self.new_configs:
                # All fields are set empty, no new configuration, will set everything to dhcpcd default (auto).
                return
            
            # e.g: interface eth0
            f.write("interface {}\n".format(self.nic))
            
            if self.new_configs.get('address'):
                # e.g: static ip_address=192.168.1.5
                if self.ip_version == 'ipv4':
                    f.write("static ip_address={}\n".format(self.new_configs.get('address')))
                # e.g: static ip6_address=fd51:42f8:caae:d92e::ff
                elif self.ip_version == 'ipv6':
                    f.write("static ip6_address=={}\n".format(self.new_configs.get('address')))
                
            if self.new_configs.get('gateway') and (self.ip_version == 'ipv4'):
                # e.g: static routers=192.168.1.1, not sure about ipv6 routers.
                f.write("static routers={}\n".format(self.new_configs.get('gateway')))
                
            if self.new_configs.get('dns-server') and self.new_configs.get('dns-server-secondary'):
                # e.g: static domain_name_servers=8.8.8.8 4.2.2.1
                f.write("static domain_name_servers={} {}\n".format(self.new_configs.get('dns-server'), self.new_configs.get('dns-server-secondary')))
            elif self.new_configs.get('dns-server'):
                # e.g: static domain_name_servers=8.8.8.8
                f.write("static domain_name_servers={}\n".format(self.new_configs.get('dns-server')))
            elif self.new_configs.get('dns-server-secondary'):
                # e.g: static domain_name_servers=4.2.2.1
                f.write("static domain_name_servers={}\n".format(self.new_configs.get('dns-server-secondary')))
                
            if self.new_configs.get('dns-search'):
                # e.g. example.com
                f.write("static domain_search={}\n".format(self.dns_search))
    
    def restart_net_service(self):
        """
        Restart dhcpcd service, to let the new dhcpcd.conf take effect.
        """
        if self.linux_nettool == "dhcpcd":
            subprocess.run(["sudo", "ip", "addr", "flush", self.nic])
            subprocess.run(["sudo", "systemctl", "restart", "dhcpcd.service"])
        elif self.linux_nettool == "NetworkManager":
            subprocess.run(["sudo", "nmcli", "conn", "down", self.nmcli_conn_name])
            subprocess.run(["sudo", "nmcli", "conn", "up", self.nmcli_conn_name])
 