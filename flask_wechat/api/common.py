#!/usr/bin/env python

from xml.etree import cElementTree as ET


class WeChatEncryptError(Exception):
    def __init__(self, code):
        self.code = code


class WeChatApiError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class WeChatMessage(object):
    def __init__(self, decrypted_xml):
        self.decrypted_xml = decrypted_xml
        document = ET.fromstring(decrypted_xml)
        self.document = document

    def __getitem__(self, key):
        node = self.document.find(key)
        if node is None:
            raise AttributeError('Attribute {} does not exist'.format(key))
        return node.text
