#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
import urllib
import urllib2

__version__ = '0.1.0'
__author__ = 'Liang Cha (ckmx945@gmail.com)'

'''
Python client SDK for Micro Message Public Platform API.
'''

try:
    import memcache
except Exception, e:
    print '\033[95mWrining: %s. use local filecache.\033[0m' %e


class APIError(StandardError):
    '''
    raise APIError if reciving json message indicating failure.
    '''
    def __init__(self, error_code, error_msg):
        self.error_code = error_code
        self.error_msg = error_msg
        StandardError.__init__(self, error_msg)

    def __str__(self):
        return '%s:%s' %(self.error_code, self.error_msg)


class AccessTokenError(APIError):
    '''
    raise AccessTokenError if reciving json message indicating failure.
    '''
    def __init__(self, error_code, error_msg):
        APIError.__init__(self, error_code, error_msg)

    def __str__(self):
        return APIError.__str__(self)


class JsonDict(dict):
    ' general json object that allows attributes to bound to and also behaves like a dict '

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(r"'JsonDict' object has no attribute '%s'" %(attr))
        
        def __setattr__(self, attr, value):
            self[attr] = value


def _parse_json(s):
    ' parse str into JsonDict '

    def _obj_hook(pairs):
        o = JsonDict()
        for k, v in pairs.iteritems():
            o[str(k)] = v
        return o
    return json.loads(s, object_hook = _obj_hook)


(_HTTP_GET, _HTTP_POST, _HTTP_FILE) = range(3)


def _encode_params(**kw):
    '''
    do url-encode parmeters

    >>> _encode_params(a=1, b='R&D')
    'a=1&b=R%26D'
    '''
    args = []
    body = None
    path = None
    for k, v in kw.iteritems():
        if k == 'body':
            body = v
            continue
        if k in ['pic']:
            continue
        if k  == 'path':
            path = v
            continue
        if isinstance(v, basestring):
            qv = v.encode('utf-8') if isinstance(v, unicode) else v
            args.append('%s=%s' %(k, urllib.quote(qv)))
        else:
            if v == None:
                args.append('%s=' %(k))
            else:
                qv = str(v)
                args.append('%s=%s' %(k, urllib.quote(qv)))
    return ('&'.join(args), body, path)


def _encode_multipart(**kw):
    ' build a multipart/form-data body with randomly generated boundary '
    boundary = '----------%s' % hex(int(time.time()) * 1000)
    data = []
    for k, v in kw.iteritems():
        if hasattr(v, 'read'):
            data.append('--%s' % boundary)
            filename = getattr(v, 'name', '')
            if filename == None or len(filename) == 0:
                filename = '/tmp/test.jpg'
            content = v.read()
            data.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (k, filename))
            data.append('Content-Length: %d' % len(content))
            #data.append('Content-Type: application/octet-stream')
            data.append('Content-Type: image/jpeg')
            data.append('Content-Transfer-Encoding: binary\r\n')
            data.append(content)
            break
    data.append('--%s--\r\n' % boundary)
    return '\r\n'.join(data), boundary


def _http_call(the_url, method, token,  **kw):
    '''
    send an http request and return a json object  if no error occurred.
    '''
    params = None
    boundary = None
    body = None
    path = None
    (params, body, path) = _encode_params(**kw)
    if method == _HTTP_FILE:
        the_url = the_url.replace('https://api.', 'http://file.api.')
        body, boundary = _encode_multipart(**kw)  
    if token == None:
        http_url = '%s?%s' %(the_url, params)
    else:
        #the_url = the_url + '?access_token=' + token
        the_url = '%s?access_token=%s' %(the_url, token)
        http_url = '%s&%s' %(the_url, params) if (method == _HTTP_GET or method == _HTTP_FILE) else the_url
    http_body = str(body) if (method == _HTTP_POST) else body
    req = urllib2.Request(http_url, data = http_body)
    if boundary != None:
        req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
    try:
        resp = urllib2.urlopen(req, timeout = 5)
        body = resp.read()
        resp.close()
        try:
            rjson = _parse_json(body)
        except Exception, e:
            if resp.getcode() != 200:
                raise e
            if resp.headers['Content-Type'] == 'image/jpeg':
                if path == None:
                    path = './WX_%d.jpg' %(int(time.time()))
            else:
                raise e
            try:
                fd = open(path, 'wb')
                fd.write(body)
            except Exception, e:
                raise e
            fd.close()
            return _parse_json('{"path":"%s"}' %(path))
        if hasattr(rjson, 'errcode') and rjson['errcode'] != 0:
            if str(rjson['errcode']) in ('40001', '40014', '41001', '42001'):
                raise AccessTokenError(str(rjson['errcode']), rjson['errmsg'])
            raise APIError(str(rjson['errcode']), rjson['errmsg'])
        return rjson
    except urllib2.HTTPError, e:
        try:
            rjson = _parse_json(e.read())
        except:
            rjson = None
            if hasattr(rjson, 'errcode'):
                if str(rjson['errcode']) in ('40001', '40014', '41001', '42001'):
                    raise AccessTokenError(str(rjson['errcode']), rjson['errmsg'])
                raise APIError(rjson['errcode'], rjson['errmsg'])
        raise e


class filecache:
    '''
    the information is temporarily saved to the file.
    '''
    def __init__(self, path, create = False):
        self.path = path
        self.dict_data = None
        fd = None
        try:
            fd = open(self.path, 'rb')
        except Exception, e:
            #print 'filecache open error:', e
            if not create:
                return None
            else:
                fd = open(self.path, 'wb')
                fd.close()
                fd = open(self.path, 'rb')
        data = fd.read()
        if len(data) == 0:
            data = '{}'
        self.dict_data = eval(data)
        fd.close()

    def get(self, key):
        if self.dict_data.has_key(key):
            return self.dict_data[key]
        return None

    def set(self, key, value, time = 0):
        if self.dict_data.has_key(key):
            self.dict_data[key] = value
        else:
            self.dict_data.update({key:value})

    def delete(self, key, time = 0):
        if self.dict_data.has_key(key):
            del self.dict_data[key]

    def save(self):
        fd = open(self.path, 'wb')
        fd.write(repr(self.dict_data))
        fd.close()

    def __str__(self):
        data = []
        for key in self.dict_data.keys():
            data += ['"%s":"%s"' %(str(key), str(self.dict_data[key]))]
        return '{%s}' %(', '.join(data))


class WeiXinClient(object):
    '''
    API clinet using synchronized invocation.

    >>> fc = False
    'use memcache save access_token, otherwise use filecache, path=[file_path | ip_addr]'
    '''
    def __init__(self, appID, appsecret, fc = False, path = '127.0.0.1:11211'):
        self.api_url = 'https://api.weixin.qq.com/cgi-bin/'
        self.app_id = appID
        self.app_secret = appsecret
        self.access_token = None
        self.expires = 0
        self.fc = fc
        self.file_cache = None
        if not self.fc:
            self.mc = memcache.Client([path], debug = 0)
        else:
            self.file_cache = '%s/access_token' %(path)
            self.mc = filecache(self.file_cache, True)

    def request_access_token(self):
        token_key = 'access_token_%s' %(self.app_id)
        expires_key = 'expires_%s' %(self.app_id)
        access_token = self.mc.get(token_key)
        expires = self.mc.get(expires_key)
        if access_token == None or expires == None or \
                int(expires) < int(time.time()):
            rjson =_http_call(self.api_url + 'token', _HTTP_GET, \
                None, grant_type = 'client_credential', \
                appid = self.app_id, secret = self.app_secret)
            self.access_token = str(rjson['access_token'])
            self.expires = int(time.time()) + int(rjson['expires_in'])
            self.mc.set(token_key, self.access_token, \
                    time = self.expires - int(time.time()))
            self.mc.set(expires_key, str(self.expires), \
                    time = self.expires - int(time.time()))
            if self.fc:
                self.mc.save()
        else:
            self.access_token = str(access_token)
            self.expires = int(expires)

    def del_access_token(self):
        import os
        token_key = 'access_token_%s' %(self.app_id)
        expires_key = 'expires_%s' %(self.app_id)
        self.access_token = None 
        self.expires = 0
        if self.fc:
            os.remove(self.file_cache)
        else:
            self.mc.delete(token_key)
            self.mc.delete(expires_key)

    def refurbish_access_token(self):
        self.del_access_token()
        self.request_access_token()

    def set_access_token(self, token, expires):
        self.access_token = token
        self.expires = expires

    def is_expires(self):
        return not self.access_token or int(time.time()) >= (self.expires - 10)

    def __getattr__(self, attr):
        return _Callable(self, attr)

    def __str__(self):
        return 'url=%s\napp_id=%s\napp_secret=%s\naccess_token=%s\nexpires=%d' \
            %(self.api_url, self.app_id, self.app_secret, self.access_token, self.expires)


class _Executable(object):

    def __init__(self, client, method, path):
        self._client = client
        self._method = method
        self._path = path

    def __call__(self, **kw):
        return _http_call('%s%s' %(self._client.api_url, self._path), \
            self._method, self._client.access_token, **kw)

    def __str__(self):
        return '_Executable (%s)' %(self._path)

    __repr__ = __str__



class _Callable(object):

    def __init__(self, client, name):
        self._client = client
        self._name = name

    def __getattr__(self, attr):
        if attr == '_get':
            return _Executable(self._client, _HTTP_GET, self._name)
        if attr == 'post':
            return _Executable(self._client, _HTTP_POST, self._name)
        if attr == 'file':
            return _Executable(self._client, _HTTP_FILE, self._name)
        name = '%s/%s' %(self._name, attr)
        return _Callable(self._client, name)

    def __str__(self):
        return '_Callable (%s)' %(self._name)

def test():
    ' test the API '
    pass

if __name__ == '__main__':
    test()
