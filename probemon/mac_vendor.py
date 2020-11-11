#!/usr/bin/env python3
import requests
import json

def get_mac_vendor(mac):
    URLs = ['http://macvendors.co/api/%s', 'https://api.macvendors.com/%s', 'http://www.macvendorlookup.com/api/v2/%s', ]
    vendor = ""
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

