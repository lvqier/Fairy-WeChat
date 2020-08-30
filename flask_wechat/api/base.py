#!/usr/bin/env python

import base64
import json
from abc import ABC

import requests
from Crypto.Cipher import AES

from .common import WeChatApiError


class BaseApi(ABC):
    def post(self, url, params=None, data=None, content_type=None):
        _ = self
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        # content_type = response.headers.get('Content-Type', 'application/json') if not content_type else content_type
        # print(content_type)
        # print('--> result:', response.text)
        # if not content_type.startswith('application/json'):
        #     return response

        result = json.loads(response.content.decode('utf-8'))
        errcode = result.get('errcode', 0)
        if errcode != 0:
            raise WeChatApiError(errcode, result.get('errmsg'))
        return result

    def get(self, url, params=None):
        response = requests.get(url, params=params)
        result = json.loads(response.content.decode('utf-8'))
        errcode = result.get('errcode', 0)
        if errcode != 0:
            raise WeChatApiError(errcode, result.get('errmsg'))
        return result

    def _aes_decrypt(self, encdata, key=None, iv=None):
        print('>>> encdata: %s' % encdata)
        print('>>>     key: %s' % key)
        print('>>>      iv: %s' % iv)
        encdata = base64.decodestring(encdata.encode())
        key = base64.decodestring(key.encode())
        iv = base64.decodestring(iv.encode())
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data = cipher.decrypt(encdata)
        padding_length = data[-1]
        data = data = data[:-padding_length]
        return data.decode('utf-8')
