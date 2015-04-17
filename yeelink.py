#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time
import json
import urllib
import urllib2

__version__ = '0.1.0'
__author__ = 'Liang Cha (ckmx945@gmail.com)'

'''
Python client SDK for YeeLink API.
'''

_API_VERSION = 'v1.0'
(_HTTP_GET, _HTTP_POST, _HTTP_PUT, _HTTP_DELETE) = range(4)


def current_time():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def _http_call(url, api_key, method, data):
    '''
    send an http request and return a rdic or list object if no error occurred.
    '''
    body = None
    boundary = None
    base_url = 'http://api.yeelink.net'
    the_url = '%s/%s%s' %(base_url, _API_VERSION, url)
    if method == _HTTP_PUT:
        the_url += '?method=put'
    if method == _HTTP_DELETE:
        the_url += '?method=delete'
    if hasattr(data, 'read'):
        #body, boundary = _encode_multipart(data)
        body = data.read()
    else:
        body = data
    req = urllib2.Request(the_url, data = body)
    req.add_header('U-ApiKey', api_key)
    if boundary != None:
        req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
    try:
        resp = urllib2.urlopen(req, timeout = 5)
        resp_body = resp.read()
        #print resp_body
        try:
            rdict = eval(resp_body)
        except SyntaxError:
            return None
        except TypeError:
            return resp_body
        return rdict
    except urllib2.HTTPError, e:
        raise e


class base(object):

    def __init__(self):
        pass

    def create(self):
        pass

    def check(self):
        pass

    def list(self):
        pass

    def edit(self):
        pass

    def delete(self):
        pass


class device(base):

    def __init__(self, api_key):
        self.api_key = api_key

    def create(self, data):
        return _http_call('/devices', self.api_key, _HTTP_POST, data)

    def list(self):
        return _http_call('/devices', self.api_key, _HTTP_GET, None)


    def edit(self, device_id, data):
        url = '/device/%s' %device_id 
        return _http_call(url, self.api_key, _HTTP_PUT, data)

    def check(self, device_id, data):
        url = '/device/%s' %device_id 
        return _http_call(url, self.api_key, _HTTP_GET, None)

    def delete(self, device_id, data):
        url = '/device/%s' %device_id 
        return _http_call(url, self.api_key, _HTTP_DELETE, None)


class sensor(base):

    def __init__(self, api_key):
        self.api_key = api_key

    def create(self, device_id, data):
        url = '/device/%s/sensors' %device_id 
        return _http_call(url, self.api_key, _HTTP_POST, data)

    def list(self, device_id):
        url = '/device/%s/sensors' %device_id 
        return _http_call(url, self.api_key, _HTTP_GET, None)

    def edit(self, device_id, sensor_id, data):
        url = '/device/%s/sensor/%s' %(device_id, sensor_id)
        return _http_call(url, self.api_key, _HTTP_PUT, data)

    def check(self, device_id, sensor_id):
        url = '/device/%s/sensor/%s' %(device_id, sensor_id)
        return _http_call(url, self.api_key, _HTTP_GET, None)

    def delete(self, device_id, sersor_id):
        url = '/device/%s/sensor/%s' %(device_id, sensor_id)
        return _http_call(url, self.api_key, _HTTP_DELETE, None)


class datapoint(base):

    def __init__(self, api_key):
        self.api_key = api_key

    def create(self, device_id, sensor_id, data):
        url = '/device/%s/sensor/%s/datapoints' %(device_id, sensor_id)
        return _http_call(url, self.api_key, _HTTP_POST, data)

    def check(self, device_id, sensor_id, key):
        url = '/device/%s/sensor/%s/datapoint/%s' %(device_id, sensor_id, key)
        return _http_call(url, self.api_key, _HTTP_GET, None)

    def edit(self, device_id, sensor_id, key, data):
        url = '/device/%s/sensor/%s/datapoint/%s' %(device_id, sensor_id, key)
        return _http_call(url, self.api_key, _HTTP_PUT, data)

    def delete(self, device_id, sensor_id, key):
        url = '/device/%s/sensor/%s/datapoint/%s' %(device_id, sensor_id, key)
        return _http_call(url, self.api_key, _HTTP_DELETE, None)


class image:

    def __init__(self, api_key):
        self.api_key = api_key

    def upload(self, device_id, sensor_id, fd):
        url = '/device/%s/sensor/%s/photos' %(device_id, sensor_id)
        return _http_call(url, self.api_key, _HTTP_POST, fd)

    def get_info(self, device_id, sensor_id, key):
        url = '/device/%s/sensor/%s/photo/info/%s' %(device_id, sensor_id, key)
        return _http_call(url, self.api_key, _HTTP_GET, None)

    def get_content(self, device_id, sensor_id, key, path):
        url = '/device/%s/sensor/%s/photo/content/%s' %(device_id, sensor_id, key)
        data = _http_call(url, self.api_key, _HTTP_GET, None)
        fd = open(path, 'wb')
        fd.write(data)
        return None


class YeeLinkClient:

    def __init__(self, api_key):
        self.device = device(api_key)
        self.sensor = sensor(api_key)
        self.datapoint = datapoint(api_key)
        self.image = image(api_key)
        self.api_key = api_key

    def history(self, device, sensor, start, end, interval=1, page=1):
        url = '/device/%s/sensor/%s.json?start=%s&end=%s&interval=%d&page=%d' \
                %(device, sensor, start, end, interval, page)
        return _http_call(url, self.api_key, _HTTP_GET, None)


def test():
    pass


if __name__ == '__main__':
    test()
