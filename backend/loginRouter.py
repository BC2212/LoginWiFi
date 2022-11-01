#!/usr/bin/python

import routeros_api

connection = routeros_api.RouterOsApiPool(
    host='192.168.88.1',
    username='wifiapi',
    password='wifilogin',
    plaintext_login=True)
api = connection.get_api()
