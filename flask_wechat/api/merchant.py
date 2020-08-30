#!/usr/bin/env python

import hashlib
import hmac
import random
import xml.etree.ElementTree as ET

import requests

from .common import WeChatApiError


class MerchantMessage(dict):
    def __init__(self, params=None):
        if params is not None:
            self.update(params)

    @classmethod
    def fromstring(cls, content):
        message = cls()
        xml = ET.fromstring(content)
        for child in xml.getchildren():
            message[child.tag] = child.text
        message.content = content
        return message

    def tostring(self):
        xml = ET.Element('xml')
        for k in self:
            node = ET.Element(k)
            node.text = str(self[k])
            xml.append(node)
        return ET.tostring(xml).decode()


class BaseMerchantApi(object):
    RANDOM_ALT_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self, appid, merchant_id, key):
        self.appid = appid
        self.merchant_id = merchant_id
        self.key = key

    def request(self, url, params):
        params = self.fill_common_params(params)
        message = MerchantMessage(params)
        data = message.tostring()
        print('merchant call {}, data {}'.format(url, str(data)))
        response = requests.post(url, data=data)
        message = MerchantMessage.fromstring(response.content)
        return self.check_message(message)

    def check_message(self, message):
        return_code = message['return_code']
        if return_code == 'FAIL':
            raise WeChatApiError(return_code, message['return_msg'])
        sign = self.sign(message)
        if not sign == message['sign']:
            # raise WeChatApiError('FAIL', '签名校验失败')
            print('check signature of response message failed')
        if message['result_code'] == 'FAIL':
            raise WeChatApiError(message['err_code'], message['err_code_des'])
        for k in ['appid', 'mch_id', 'nonce_str', 'sign_type', 'sign', 'return_code', 'return_msg', 'result_code', 'result_msg', 'err_code', 'err_code_des']:
            if k in message:
                message.pop(k)
        return message

    def fill_common_params(self, params):
        params['appid'] = self.appid
        params['mch_id'] = self.merchant_id
        params['nonce_str'] = self.random_str(length=32)
        # params['sign_type'] = 'MD5'
        params['sign'] = self.sign(params)
        return params

    def random_str(self, length=32, alt_chars=None):
        if alt_chars is None:
            alt_chars = self.RANDOM_ALT_CHARS
        chars = [alt_chars[random.randint(0, len(alt_chars) - 1)] for i in range(length)]
        return ''.join(chars)

    def sign(self, params):
        method = params.get('sign_type', 'MD5')
        kvs = []
        for k in params:
            if k == 'sign':
                continue
            kvs.append('{}={}'.format(k, params[k]))
        kvs.sort()
        kvs.append('key={}'.format(self.key))
        tosign_data = '&'.join(kvs)
        if method == 'MD5':
            return self.sign_md5(tosign_data)
        elif method == 'HMAC-SHA256':
            return self.sign_hmac_sha256(tosign_data)
        assert False, 'sign method {} not supported'.format(method)

    def sign_hmac_sha256(self, data):
        hmac_sha256 = hmac.new(self.key, data.encode(), digestmod=hashlib.sha256)
        return hmac_sha256.hexdigest().upper()

    def sign_md5(self, data):
        md5 = hashlib.md5(data.encode())
        return md5.hexdigest().upper()


class OrdinaryMerchantApi(BaseMerchantApi):
    '''
    普通商户
    '''
    def __init__(self, appid, merchant_id, key):
        super(OrdinaryMerchantApi, self).__init__(appid, merchant_id, key)

    def unifinedorder(self, body, out_trade_no, total_fee, spbill_create_ip, notify_url, trade_type, **kwargs):
        openid = kwargs.get('openid')
        assert trade_type != 'JSAPI' or openid is not None, 'openid should be provided when trade_type is JSAPI'
        params = {
            'body': body,
            'out_trade_no': out_trade_no,
            'total_fee': total_fee,
            'spbill_create_ip': spbill_create_ip,
            'notify_url': notify_url,
            'trade_type': trade_type
        }
        for key in kwargs:
            value = kwargs[key]
            if value is None:
                continue
            params[key] = value
        return self.request('https://api.mch.weixin.qq.com/pay/unifiedorder', params)

    def payment_notify(self, payload):
        message = MerchantMessage.fromstring(payload)
        return self.check_message(message)

    def orderquery(self, transaction_id=None, out_trade_no=None):
        params = {}
        if transaction_id is not None:
            params['transaction_id'] = transaction_id
        elif out_trade_no is not None:
            params['out_trade_no'] = out_trade_no
        else:
            assert False, 'both transaction_id and out_trade_no is not provided'
        return self.request('https://api.mch.weixin.qq.com/pay/orderquery')
