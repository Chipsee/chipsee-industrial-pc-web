from lib.chipsee_board import board
import ipaddress
import subprocess

class IpConfig(object):
    """
    Set static IP from user input form.
    Raspberry Pi based system (CM4) uses dhcpcd to control network.
    It reads/writes to /etc/dhcpcd.conf file to control static IP of a nic.
    """
    def __init__(self):
        self.dhcpcd_conf_path = '/etc/dhcpcd.conf'
        self.nics = board.devices().get("nics") or {}
        self.available_configs = {
            'v4Address': 'IPv4 Address',
            'v6Address': 'IPv6 Address',
            'router': 'Router',
            'dns-server': 'Primary DNS server',
            'dns-server-secondary': 'Secondary DNS server',
            # 'dns-search' is set later.
        }
    
    def handle_form(self, form):
        self.new_configs = {}
        self.form_errors = []
        self.validate_form(form)
        if self.form_errors:
            return "{} error(s) prohibited IP from being set, please check the error messages below:".format(len(self.form_errors)), self.form_errors
        else:
            self.update_config()
            return "Updated IP settings for {}.".format(self.nic), self.form_errors

    def validate_form(self, form):
        """
        Validate user input form from HTML. 
        Some settings should be valid IP format that will be stored in the dhcpcd.conf file later.
        """
        for key in self.available_configs:
            self.validate_ip_related_field(field_name=key, form=form)
        self.validate_dns_search_field(form)
        self.validate_nic_field(form)
      
    def update_config(self):
        """
        Mostly read/write a dhcpcd.conf file.
        Redundent settings will be removed, new settings will be appended to the end of this file.
        """
        self.load_current_dhcpcd_conf()
        self.remove_nic_settings_from_dhcpcd_conf()
        self.append_new_settings_to_dhcpcd_conf()
        self.restart_dhcpcd_service()
        
    def validate_dns_search_field(self, form):
        if form['dns-search']:
            self.new_configs['dns-search'] = form['dns-search']
            
    def validate_nic_field(self, form):
        nic = form.get('nic')
        if not nic:
            self.form_errors.append("Please select a network interface.")
            return
        if nic in self.nics:
            self.nic = nic
        else:
            avai_nics = " ".join(list(self.nics.keys()))
            error = "'{}' is not a valid network interface card of this PC, available nics are: {}.".format(nic, avai_nics)
            self.form_errors.append(error)
            
    def validate_ip_related_field(self, field_name, form):
        """
        'v4Address', 'v6Address', 'router', 'dns-server' and 'dns-server-secondary' should be of type ipaddress.ip_address.
        If they're not in the correct format, user might have input a wrong IP, 
        This method adds the invalid field to error message to inform the user.
        """
        if not form[field_name]:
            return
        try:
            new_ip_value = ipaddress.ip_address(form[field_name])
            self.new_configs[field_name] = str(new_ip_value)
        except ValueError as e:
            self.form_errors.append("{} field is invalid.".format(self.available_configs.get(field_name)))
        
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
            
            if self.new_configs.get('v4Address'):
                # e.g: static ip_address=192.168.1.5
                f.write("static ip_address={}\n".format(self.new_configs.get('v4Address')))
                
            if self.new_configs.get('v6Address'):
                # e.g: static ip6_address=fd51:42f8:caae:d92e::ff
                f.write("static ip6_address=={}\n".format(self.new_configs.get('v6Address')))
                
            if self.new_configs.get('router'):
                # e.g: static routers=192.168.1.1
                f.write("static routers={}\n".format(self.new_configs.get('router')))
                
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
                # e.g. www.example.com
                f.write("static domain_search={}\n".format(self.dns_search))
    
    
    def restart_dhcpcd_service(self):
        """
        Restart dhcpcd service, to let the new dhcpcd.conf take effect.
        """
        subprocess.run(["sudo", "ip", "addr", "flush", self.nic])
        subprocess.run(["sudo", "systemctl", "restart", "dhcpcd.service"])
 