#!/usr/bin/env python

WX_COMPONENT_APPID = 'wxf2784b1b713015ce'
WX_COMPONENT_SECRET = 'b0723ee02105269024732c157d8454f5'
WX_COMPONENT_TOKEN = 'EasierCardasdfg123456'
WX_COMPONENT_ENCKEY = 'dkigjedkifjepkigjedkigsedkigqedkigjldkiwwe4'

from WXBizMsgCrypt import WXBizMsgCrypt

message = '''<xml>
    <AppId><![CDATA[wxf2784b1b713015ce]]></AppId>
    <Encrypt><![CDATA[296xUZYSCx8KSVE3V3ZH9Lju2BZLhkAJkg6dd+HSZXaqWx2jtRdBdGJ3SLok1nl/fU7otVqX3h4H5Ww/bxWpaofJRIvbb6lH9VK3EWr136ztyLZvO+mHyoRuMC51MkQmL+H5QBRH4Mz1BjEjKEBTdF8KMD+LIE1bjT2dOJWWVkT8PL/qG6iDhAWghkXeMDSyHQUj7bb7L7puByUmGrANuKg2eg9m7jDD+QTFUNqOGMvHB8bd25admmKC1LC9gwDP0vbyfqwXOhw0kEvzO7JJXcFHHcrNhAiEgzqURvUunNISWfd7Jav/YwOJCXdrilAqMUy2pHwC3eM+mQyIN2H/szlA27s7U5skpESHGde8xVIZNAiOb65vit4SMxUAtJdo1IfzolEtJocIPI9kAx4yAG1IpRaHIB6+K0tHvUxbQWUwrCw4EiNsSCORxnR+l+44MsvCGYYcvlhkvEYELqEorw==]]></Encrypt>
</xml>'''
timestamp = '1536679149'
nonce = '1640336628'
signature = '3c5a784eac663f7cc9707b230a1ea4e8732b0898'

msg_crypt = WXBizMsgCrypt(WX_COMPONENT_TOKEN, WX_COMPONENT_ENCKEY, WX_COMPONENT_APPID)
ret, d = msg_crypt.DecryptMsg(message, signature, timestamp, nonce)
print(ret)
print(d)
