#!/usr/bin/python3

import json
import sys, os

from flask import Flask, render_template, redirect, url_for, request, session

HOME_DIR = os.environ['HOME_DIR']
sys.path.insert(0, HOME_DIR)

import dnx_configure.dnx_configure as configure
import dnx_configure.dnx_validate as validate

from dnx_configure.dnx_constants import CFG, DATA, INVALID_FORM
from dnx_configure.dnx_file_operations import load_configuration
from dnx_configure.dnx_exceptions import ValidationError
from dnx_configure.dnx_system_info import System

def load_page():
    whitelist = load_configuration('whitelist')

    for domain, info in whitelist['domain'].items():
        st_offset = System.calculate_time_offset(info['time'])

        domain['time'] = System.format_date_time(st_offset)

    whitelist_settings = {
        'domain_whitelist': whitelist['domain'], 'exceptions': whitelist['exception'],
        'ip_whitelist':  whitelist['ip_whitelist']
    }

    return whitelist_settings

def update_page(form):
    if ('wl_add' in form):
        whitelist_settings = {
            'domain': form.get('domain', DATA.INVALID),
            'timer': validate.get_convert_int(form, 'rule_length')
        }
        if (DATA.INVALID in whitelist_settings.values()):
            return INVALID_FORM

        try:
            validate.domain(whitelist_settings['domain'])
            validate.timer(whitelist_settings['timer'])
        except ValidationError as ve:
            return ve
        else:
            configure.add_proxy_domain(whitelist_settings, ruleset='whitelist')

    elif ('wl_remove' in form):
        domain = form.get('wl_remove', DATA.INVALID)

        if (domain is DATA.INVALID):
            return INVALID_FORM

        configure.del_proxy_domain(domain, ruleset='whitelist')

    elif ('exc_add' in form):
        exception_settings = {
            'domain': form.get('domain', DATA.INVALID),
            'reason': form.get('reason', DATA.INVALID),
            'action': CFG.ADD
        }
        if (DATA.INVALID in exception_settings.values()):
            return INVALID_FORM

        try:
            validate.domain(exception_settings['domain'])
            validate.standard(exception_settings['reason'])
        except ValidationError as ve:
            return ve
        else:
            configure.set_proxy_exception(exception_settings, ruleset='whitelist')

    elif ('exc_remove' in form):
        exception_settings = {
            'domain': form.get('exc_remove', DATA.INVALID),
            'reason': None,
            'action': CFG.DEL
        }
        if (exception_settings['domain'] is DATA.INVALID):
            return INVALID_FORM

        configure.set_proxy_exception(exception_settings, ruleset='whitelist')

    # TODO: this should not restrict ips to only "local_net" now that we have multiple interfaces.
    # we should have the user select which interface it will be active on so we can properly validate the
    # ip address falls within that subnet.

    elif ('ip_wl_add' in form):
        whitelist_settings = {
            'ip': form.get('ip_wl_ip', DATA.INVALID),
            'user':form.get('ip_wl_user', DATA.INVALID),
            'type': form.get('ip_wl_type', DATA.INVALID)
        }
        if (DATA.INVALID in whitelist_settings.values()):
            return INVALID_FORM

        try:
            validate.add_ip_whitelist(whitelist_settings)
        except ValidationError as ve:
            return ve
        else:
            configure.add_proxy_ip_whitelist(whitelist_settings)

    elif ('ip_wl_remove' in form):
        whitelist_ip = form.get('ip_wl_ip', DATA.INVALID)

        if (whitelist_ip is DATA.INVALID):
            return INVALID_FORM

        try:
            validate.ip_address(whitelist_ip)
        except ValidationError as ve:
            return ve
        else:
            configure.del_proxy_ip_whitelist(whitelist_ip)

    else:
        return INVALID_FORM