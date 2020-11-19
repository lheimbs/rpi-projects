#!/usr/bin/env python3
import netaddr
import requests
import json

def get_mac_vendor(mac):
    URLs = ['http://macvendors.co/api/%s', 'http://www.macvendorlookup.com/api/v2/%s', 'https://api.macvendors.com/%s',]
    vendor = 'UNKNOWN'

    try:
        parsed_mac = netaddr.EUI(mac)
        vendor = parsed_mac.oui.registration().org
    except netaddr.core.NotRegisteredError as e:
        for url in URLs:
            r = requests.get(url % mac)
            if r and r.status_code == 200:
                try:
                    # print(r.json())
                    res = r.json()
                    if 'error' in res:
                        continue
                    if 'result' in res.keys() and 'company' in res['result'].keys():
                        vendor = res['result']['company']
                        break
                except json.JSONDecodeError:
                    # print(r.text)
                    if r.text:
                        vendor = r.text
                        break
    return vendor

