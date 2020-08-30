#!/usr/bin/env python

import time
from urllib import parse

from flask import request

from .api import OrdinaryMerchantApi, MerchantMessage


class OrdinaryMerchantClient(object):
    def __init__(self, app=None):
        if app:
            self.init_app(app)
        self.payment_notify_handlers = []

    def init_app(self, app, appid=None, trade_type='JSAPI'):
        self.flask_app = app
        self.appid = appid
        self.trade_type = trade_type
        self.mch_id = app.config['WECHAT_MERCHANT_MCHID']
        key = app.config['WECHAT_MERCHANT_KEY']
        self.merchant_api = OrdinaryMerchantApi(appid, self.mch_id, key)

    def unifinedorder(self, body, out_trade_no, total_fee, spbill_create_ip, notify_url, **kwargs):
        result = self.merchant_api.unifinedorder(body, out_trade_no, total_fee, spbill_create_ip, notify_url, self.trade_type, **kwargs)
        return result['prepay_id']

    def get_payment_data(self, **kwargs):
        # prepay_id = kwargs['prepay_id']
        result = {
            'appId': self.appid,
            'timeStamp': int(time.time()),
            'nonceStr': self.merchant_api.random_str(),
            'package': parse.urlencode(kwargs),
            'signType': 'MD5'
        }
        result['paySign'] = self.merchant_api.sign(result)
        result.pop('appId')
        return result

    def payment_response(self):
        message = self.merchant_api.payment_notify(request.data)
        for handler in self.payment_notify_handlers:
            handler(message['out_trade_no'], message)
        result = MerchantMessage({'return_code': 'SUCCESS', 'return_msg': 'OK'})
        return result.tostring()

    def payment_notify_handler(self, func):
        self.payment_notify_handlers.append(func)
        return func

    def orderquery(self, transaction_id=None, out_trade_no=None):
        return self.merchant_api.orderquery(transaction_id=transaction_id, out_trade_no=out_trade_no)
