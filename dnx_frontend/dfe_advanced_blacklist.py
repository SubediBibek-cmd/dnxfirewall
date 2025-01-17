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
    blacklist = load_configuration('blacklist')

    for domain, info in blacklist['domain'].items():
        st_offset = System.calculate_time_offset(info['time'])

        domain['time'] = System.format_date_time(st_offset)

    blacklist_settings = {
        'domain_blacklist': blacklist['domain'],
        'exceptions': blacklist['exception']
    }

    return blacklist_settings

def update_page(form):
    if ('bl_add' in form):
        blacklist_settings = {
            'domain': form.get('domain', DATA.INVALID),
            'timer': validate.get_convert_int(form, 'rule_length')
        }
        if (DATA.INVALID in blacklist_settings.values()):
                return INVALID_FORM

        try:
            validate.domain(blacklist_settings['domain'])
            validate.timer(blacklist_settings['timer'])
        except ValidationError as ve:
            return ve
        else:
            configure.add_proxy_domain(blacklist_settings, ruleset='blacklist')

    elif ('bl_remove' in form):
        domain = form.get('bl_remove', DATA.INVALID)

        if (domain is DATA.INVALID):
            return INVALID_FORM

        configure.del_proxy_domain(domain, ruleset='blacklist')

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
            configure.set_proxy_exception(exception_settings, ruleset='blacklist')

    elif ('exc_remove' in form):
        exception_settings = {
            'domain': form.get('exc_remove', DATA.INVALID),
            'reason': None,
            'action': CFG.DEL
        }

        if (DATA.INVALID in exception_settings.values()):
            return INVALID_FORM

        configure.set_proxy_exception(exception_settings, ruleset='blacklist')

    else:
        return INVALID_FORM
