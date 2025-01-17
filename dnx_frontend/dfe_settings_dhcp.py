#!/usr/bin/python3

import sys, os
import time
import json

from types import SimpleNamespace

HOME_DIR = os.environ['HOME_DIR']
sys.path.insert(0, HOME_DIR)

import dnx_configure.dnx_configure as configure
import dnx_configure.dnx_validate as validate

from dnx_configure.dnx_constants import CFG, DATA, INVALID_FORM, DHCP
from dnx_iptools.dnx_protocol_tools import convert_mac_to_string as mac_str
from dnx_configure.dnx_file_operations import load_configuration
from dnx_configure.dnx_exceptions import ValidationError
from dnx_configure.dnx_system_info import Services, System

def load_page():
    dhcp_server = load_configuration('dhcp_server')

    dhcp_settings = dhcp_server['interfaces']

    leases = []
    for ip, (status, handout_time, mac) in dhcp_server['leases'].items():
        # ensuring only leased status entries get included
        if (status != -4): continue

        offset_time = System.calculate_time_offset(handout_time)
        handout_time = System.format_date_time(offset_time)

        leases.append((ip, handout_time, mac_str(mac)))

    leases.sort()

    dhcp_settings.update({
        'reservations': [(mac_str(mac), info) for mac, info in dhcp_server['reservations'].items()],
        'leases': leases
    })

    return dhcp_settings

#TODO: figure out a way to ensure duplicate ip addresses cannot have a reservation created. currently we
# use the mac address as the key/identifier which would allow for different macs to be configured with the
# same ip address.
def update_page(form):

    print(form)

    if ('dhcp_res_add' in form):
        dhcp_settings = {
            'zone': form.get('zone', DATA.INVALID),
            'mac': form.get('mac_address', ''),
            'ip': form.get('ip_address', DATA.INVALID),
            'description': form.get('description', DATA.INVALID)
        }

        if (DATA.INVALID in dhcp_settings.values()):
            return INVALID_FORM

        try:
            validate.dhcp_reservation(dhcp_settings)

            # will raise exception if ip address is already reserved
            configure.set_dhcp_reservation(dhcp_settings, CFG.ADD)
        except ValidationError as ve:
            return ve

    # Matching DHCP reservation REMOVE and sending to configuration method.
    elif ('dhcp_res_remove' in form):
        mac_address = form.get('dhcp_res_remove', None)
        if (not mac_address):
            return INVALID_FORM

        try:
            validate.mac_address(mac_address)
        except ValidationError as ve:
            return ve
        else:
            dhcp_settings = {'mac': mac_address.replace(':', '')}

            configure.set_dhcp_reservation(dhcp_settings, CFG.DEL)

    elif ('dhcp_lease_remove' in form):
        ip_addr = form.get('dhcp_lease_remove', None)
        if (not ip_addr):
            return INVALID_FORM

        try:
            validate.ip_address(ip_addr)

            configure.remove_dhcp_lease(ip_addr)
        except ValidationError as ve:
            return ve

    elif ('general_settings' in form):
        server_settings = {
            'interface': form.get('interface', DATA.INVALID),

            # NOTE: switch does not post field if disabled. if not present, the server will disable the
            # corresponding field as normal.
            'enabled': True if form.get('server_enabled', False) else False,
            'icmp_check': True if form.get('icmp_check', False) else False,

            'lease_range': {
                'start': validate.get_convert_int(form, 'start'),
                'end': validate.get_convert_int(form, 'end')
            }
        }

        if (DATA.INVALID in server_settings.values()):
                return INVALID_FORM

        try:
            validate.dhcp_general_settings(server_settings)
        except ValidationError as ve:
            return ve

        else:
            configure.set_dhcp_settings(server_settings)

    else:
        return INVALID_FORM
