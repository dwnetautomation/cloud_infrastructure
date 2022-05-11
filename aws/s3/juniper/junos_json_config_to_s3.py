#!/usr/bin/python3.6

import subprocess
import yaml
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import MD5
import base64
import boto3
import json

passphrase = '<PASSPHRASE>'.encode()
settings_file = open('/settings/settings.yaml', 'r')
settings = yaml.safe_load(settings_file)
BLOCK_SIZE=16
def trans(key):
    return MD5.new(key).digest()
def passhash(encrypted, passphrase):
    passphrase = trans(passphrase)
    encrypted = base64.b64decode(encrypted)
    IV = encrypted[:BLOCK_SIZE]
    aes = AES.new(passphrase, AES.MODE_CFB, IV)
    return aes.decrypt(encrypted[BLOCK_SIZE:])
user = settings['netsvc_acct']['user']
key = settings['netsvc_acct']['aws_key']
settings['netsvc_acct']['password'] = passhash(settings['netsvc_acct']['password'],passphrase)
pwd = settings['netsvc_acct']['password']
password = "".join( chr(x) for x in pwd)
settings['netsvc_acct']['aws_secret'] = passhash(settings['netsvc_acct']['aws_secret'],passphrase)
secret = settings['netsvc_acct']['aws_secret']
secret = "".join( chr(x) for x in secret)
port = '22'
host = 'gre01.lab'
devd = dict(host=host, user=user, password=password, port=port)
s3d = dict(aws_access_key_id=key, aws_secret_access_key=secret)

def upload_json_to_s3(json_config, s3d):
    session = boto3.Session(**s3d)
    s3 = session.client('s3')
    s3.put_object(Body=json.dumps(json_config), Bucket='netconfigs-uddos-lab', Key='{0}.json'.format(host))

def get_json_config(devd):
    dev = Device(**devd)
    dev.open()
    json_config = dev.rpc.get_configuration({'format':'json'})
    dev.close()
    return json_config

if __name__ == "__main__":
    json_config = get_json_config(devd)
    upload_json_to_s3(json_config, s3d)


