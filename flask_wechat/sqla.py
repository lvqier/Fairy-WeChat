#!/usr/bin/env python

import json
import time

from sqlalchemy import Column, String, Text, Integer


class WechatFuncInfo(object):
    func_map = {
        '1': '消息管理权限 ', '2': '用户管理权限', '3': '帐号服务权限', '4': '网页服务权限',
        '5': '微信小店权限', '6': '微信多客服权限', '7': '群发与通知权限 ', '8': '微信卡券权限',
        '9': '微信扫一扫权限', '10': '微信连WIFI权限', '11': '素材管理权限', '12': '微信摇周边权限',
        '13': '微信门店权限', '15': '自定义菜单权限', '16': '获取认证状态及信息',
        '17': '帐号管理权限（小程序）', '18': '开发管理与数据分析权限（小程序）',
        '19': '客服消息管理权限（小程序）', '20': '微信登录权限（小程序）',
        '21': '数据分析权限（小程序）', '22': '城市服务接口权限 ', '23': '广告管理权限',
        '24': '开放平台帐号管理权限', '25': '开放平台帐号管理权限（小程序）', '26': '微信电子发票权限',
        '30': '小程序基本信息设置权限', '41': '搜索widget的权限',
    }


class WeChatAppMixin(object):
    appid = Column(String(32))
    biz_type = Column(String(32))
    access_token = Column(String(512))
    expires_at = Column(Integer)
    refresh_token = Column(String(128))
    name = Column(String(128))
    avatar_url = Column(String(1024))
    service_type = Column(Integer)
    verify_type = Column(Integer)
    user_name = Column(String(16))
    principal_name = Column(String(128))
    business_info = Column(String(1024))
    qrcode_url = Column(String(1024))
    func_info = Column(String(128))
    biz_info = Column(Text)

    @property
    def require_func_list(self):
        if self.biz_type == 'gzh':
            funcs = [4, 2, 7, 8, 9, 24, 33]
        elif self.biz_type == 'xcx':
            funcs = [17, 18, 25, 30]
        else:
            funcs = []

        return funcs

    def update_authorization_info(self, authorization_info):
        self.access_token = authorization_info['authorizer_access_token']
        self.expires_at = int(time.time()) + int(authorization_info['expires_in'])
        self.refresh_token = authorization_info['authorizer_refresh_token']
        if 'func_info' in authorization_info:
            func_info = authorization_info['func_info']
            self.func_info = ','.join([str(item['funcscope_category']['id']) for item in func_info])

    def update_authorizer_info(self, authorizer_info):
        # print(json.dumps(authorizer_info, indent=4))
        self.name = authorizer_info.get('nick_name')
        self.avatar_url = authorizer_info.get('head_img')
        self.service_type = authorizer_info['service_type_info']['id']
        self.verify_type = authorizer_info['verify_type_info']['id']
        self.user_name = authorizer_info['user_name']
        self.principal_name = authorizer_info['principal_name']
        self.business_info = authorizer_info['business_info']
        self.qrcode_url = authorizer_info['qrcode_url']

        if 'authorization_info' in authorizer_info:
            authorization_info = authorizer_info['authorization_info']
            # authorization_appid = authorization_info['authorization_appid'] # same as wechat_app.appid
            func_info = authorization_info['func_info']
            self.func_info = ','.join([str(item['funcscope_category']['id']) for item in func_info])
            self.biz_type = 'xcx' if 'MiniProgramInfo' in authorizer_info else 'gzh'

            biz_info = {}
            biz_info_keys = ['alias', 'signature']
            for biz_info_key in biz_info_keys:
                if biz_info_key in authorizer_info:
                    biz_info[biz_info_key] = authorizer_info[biz_info_key]
            biz_info.update(authorizer_info.get('MiniProgramInfo', {}))
            self.biz_info = json.dumps(biz_info)

    def get_func_info(self):
        return [int(func_id) for func_id in self.func_info.split(',')]


class WeChatUserMixin(object):
    appid = Column(String(32))
    openid = Column(String(32))
    access_token = Column(String(512))
    expires_at = Column(Integer)
    refresh_token = Column(String(1024))
    scope = Column(String(64))
    language = Column(String(16))
    nickname = Column(String(32))
    sex = Column(Integer)
    province = Column(String(32))
    city = Column(String(32))
    mobile = Column(String(16))
    country = Column(String(32))
    avatar_url = Column(String(255))
    privilege = Column(String(64))

    def update_token(self, token):
        self.access_token = token.get('access_token')
        if isinstance(token.get('expires_in'), int):
            self.expires_at = int(time.time()) + int(token.get('expires_in'))
        self.refresh_token = token.get('refresh_token')
        self.scope = token.get('scope')

    def update_user_info(self, user_info):
        """
        兼容小程序和网页授权
        """
        self.nickname = self._get_value(user_info, ('nickname', 'nickName'))
        self.sex = self._get_value(user_info, ('sex', 'gender'))
        self.province = user_info['province']
        self.city = user_info['city']
        self.country = user_info['country']
        self.avatar_url = self._get_value(user_info, ('headimgurl', 'avatarUrl'))
        self.privilege = ','.join(user_info.get('privilege', []))
        self.language = user_info['language']

    @classmethod
    def _get_value(cls, user_info, keys):
        for k in keys:
            if k in user_info:
                return user_info[k]
