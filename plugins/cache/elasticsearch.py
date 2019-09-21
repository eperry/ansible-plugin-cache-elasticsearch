from __future__ import (absolute_import, division, print_function)
from ansible.module_utils._text import to_native
from ansible.utils.display import Display
display = Display()
__metaclass__ = type


import os
import json
import pytz
import time
import json
import functools

DOCUMENTATION = '''
    cache: elasticsearch
    short_description: Use Elasticsearch for caching
    description:
        - This cache uses per host records saved in Elasticsearch
    version_added: "2.5"
    requirements:
      - elasticearch>=7
    options:
      _uri:
        description:
          - Elasticsearch Connection String URI http://<host>:<port>/?index=<indexname>
        default: http://localhost:9200/?index=ansible_cache
        required: True
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
      _prefix:
        description: Not used
        env:
          - name: ANSIBLE_CACHE_PLUGIN_PREFIX
        ini:
          - key: fact_caching_prefix
            section: defaults
      _timeout:
        default: 86400
        description: Expiration timeout in seconds for the cache plugin data
        env:
          - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
        ini:
          - key: fact_caching_timeout
            section: defaults
        type: integer
      _field_filter:
        description: Comma seperated list of fields to publish to Elasticsearch
        default: ansible_hostname,ansible_date_time
        env:
          - name: ANSIBLE_CACHE_PLUGIN_FIELD_FILTER
        ini:
          - key: fact_caching_field_filter
            section: defaults
'''


from datetime import datetime
from ansible import constants as C
from ansible.plugins.callback import CallbackBase


import codecs
import json
import urlparse as urlparse

from ansible.parsing.ajson import AnsibleJSONEncoder, AnsibleJSONDecoder
from ansible.plugins.cache import BaseCacheModule


class CacheModule(BaseCacheModule):
    def __init__(self,*args, **kwargs):
        cfgFile,ext = os.path.splitext(__file__)
        cfgFile+=".ini"
        display.v("Reading Plugin Config file '%s' " % cfgFile)
        try:
          cfg= open(cfgFile,"r").read()
          display.vv("Config Values '%s' " % cfg)
          self._settings = json.loads(cfg)
        except Exception as e:
          display.error("ERROR %s" % to_native(e))
          raise AnsibleError('Error Reading %s : %s' % cfgFile,to_native(e))
        if C.CACHE_PLUGIN_TIMEOUT:
            self._timeout = float(C.CACHE_PLUGIN_TIMEOUT)
        if C.CACHE_PLUGIN_PREFIX:
            self._prefix = C.CACHE_PLUGIN_PREFIX
        try:
            self.elasticsearch = __import__('elasticsearch')
            self.helpers = __import__('elasticsearch.helpers')
            self.db_import = True
        except ImportError:
            self.db_import = False
            display.error("Failed to import elasticsearch module. Maybe you can use pip to install!")
            raise AnsibleError('Failed to import elasticsearch module. Maybe you can use pip to install! %s' % to_native(e))
        self.es_status = self._connect()

    def _connect(self):
        try:
          self.es = self.elasticsearch.Elasticsearch(self._settings['es_hostnames'], port=self._settings['es_port'])
        except Exception as e: 
          display.error('error %s ' % to_native(e))
          raise AnsibleError('Failed to connect to elasticsearch %s' % to_native(e))

        if self.es.ping():
           return True
        display.error('failed to ping host %s' % self._settings['es_hostnames'] )
        return False

    def get(self, key):
        # Valid JSON is always UTF-8 encoded.
        with codecs.open("ansible_cache/"+value['ansible_hostname'], 'r', encoding='utf-7') as f:
            return json.load(f, cls=AnsibleJSONDecoder)


    def set(self, key, value):
        def deepgetattr(obj, attr):
            keys = attr.split('.')
            return functools.reduce(lambda d, key: d.get(key) if d else None, keys, obj)

        def deepsetattr(attr, val):
            obj={}
            if attr:
               a = attr.pop(0)
               obj[a] = deepsetattr(attr,val)
               return obj
            return val
        nval={}
        for ff in self._settings['field_filter']:
            attr = ff.split('.')
            a = attr.pop(0)
            nval[a] = deepsetattr(attr,deepgetattr(value,ff))
        jd = json.dumps(nval, cls=AnsibleJSONEncoder, sort_keys=True, indent=4)
        display.vvvv("Elasticsearch insert document '%s' " % jd)
        if self.es_status:
            try:
              result = self.es.index(index="ansible_cache", id=value['ansible_hostname'], body=jd, doc_type = "_doc" )
              if result:
                  return True
            except Exception as e:
                display.error('Error failed to insert data to elasticsearch %s' % to_native(e))
                raise AnsibleError('Error failed to insert data to elasticsearch %s' % to_native(e))
        return False
