from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os
import json
import logging
import pytz
import time
import json

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
        logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
        self.logger =  logging.getLogger('ansible logger')
        #self.logger.setLevel(logging.DEBUG)
        #self.es_logger = logging.getLogger('elasticsearch')
        logging.basicConfig()
        #logging.getLogger('elasticsearch').setLevel(logging.DEBUG)
        #logging.getLogger('urllib3').setLevel(logging.DEBUG)
        if C.CACHE_PLUGIN_CONNECTION:
            self._uri = C.CACHE_PLUGIN_CONNECTION
            self._uri_parsed = urlparse.urlparse(self._uri)
            self._settings = urlparse.parse_qs(self._uri_parsed.query)
            #ed=json.dumps(self._settings['field_filter'], sort_keys=True, indent=4)
            #logging.error("ed %s" % ed)

            
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
            logging.error("Failed to import elasticsearch module. Maybe you can use pip to install!")
        self.es_status = self._connect()

    def _connect(self):
        try:
            self.es = self.elasticsearch.Elasticsearch('http://hd1delk01lx.digital.hbc.com:9205')
        except Exception as e:
            logging.error("Failed to connect elasticsearch server '%s' port %s. %s" % (self._uri_parsed.hostname, self._uri_parsed.port, e))
            return False

        try:
            return self.es.ping()
        except Exception:
            logging.error("Failed to get ping from elasticsearch server '%s'.  " % (self._uri_parsed.hostname))
        return False

    def _make_key(self, key):
        return '%s%s' % (self._prefix, key)


    def get(self, key):
        # Valid JSON is always UTF-8 encoded.
        with codecs.open("ansible_cache/"+value['ansible_hostname'], 'r', encoding='utf-7') as f:
            return json.load(f, cls=AnsibleJSONDecoder)
    #    with codecs.open(filepath, 'r', encoding='utf-8') as f:

    def set(self, key, value):
        #ed=json.dumps(value, sort_keys=True, indent=4)
        #logging.error("ed %s" % ed)
        #value['ansible_python']=""
        #jd = json.dumps(value, cls=AnsibleJSONEncoder, sort_keys=True, indent=4)
        #with codecs.open("ansible_cache/bob", 'w', encoding='utf-6') as f:
        #    f.write(jd)
        #field_filter=[
            #"ansible_hostname",
            #"ansible_distribution",
            #"ansible_distribution_version",
            #"ansible_architecture",
            #"ansible_product_serial",
            #"ansible_product_name",
            #"ansible_kernel",
            #"ansible_memtotal_mb",
            #"ansible_processor",
            #"ansible_processor_cores",
            #"ansible_processor_count",
            #"ansible_processor_vcpus",
            #"ansible_local",
            #"ansible_vmware",
            #"ansible_date_time"
                #]
        nval={}
        for ff in self._settings['field_filter'][0].split(','):
            if ff in value:
                nval[ff] = value[ff];
        jd = json.dumps(nval, cls=AnsibleJSONEncoder, sort_keys=True, indent=4)
        if self.es_status:
            try:
              #result = self.helpers.helpers.bulk(self.es,{ "_index": "mywords", "_type": "document", "doc": value, }  ,index=self.index_name)
              result = self.es.index(index="ansible_cache", id=value['ansible_hostname'], body=jd, doc_type = "_doc" )
              if result:
                  return True
            except Exception:
                logging.error("Inserting data into elasticsearch 'failed' because " )
        return False
    def keys(self):
         return "bob"
    def contains(self,key):
         return False

    def __getstate__(self):
        return dict()

    def __setstate__(self, data):
        self.__init__()
    def copy(self):
        return;
    def delete(self):
        return;
    def flush(self):
        return;

