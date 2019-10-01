from __future__ import (absolute_import, division, print_function)
from ansible.module_utils._text import to_native
from ansible.utils.display import Display
from ansible.errors import AnsibleError, AnsibleParserError
from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.parsing.ajson import AnsibleJSONEncoder, AnsibleJSONDecoder
from ansible.plugins.cache import BaseCacheModule
display = Display()
__metaclass__ = type


import os
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
          - Not Used see ini settings
        default: 
        required: false
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
        description: Not used 
        env:
          - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
        ini:
          - key: fact_caching_timeout
            section: defaults
        type: integer
'''

class CacheModule(BaseCacheModule):
    def __init__(self,*args, **kwargs):
        #############################################
        ####  Handle default way of configuring plugins even though we won't use it
        #############################################
        try:
          super(CacheModule, self).__init__(*args, **kwargs)
          self._uri     = self.get_option('_uri')
          self._timeout = float(self.get_option('_timeout'))
          self._prefix  = self.get_option('_prefix')
        except KeyError:
          display.deprecated('Rather than importing CacheModules directly, '
                             'use ansible.plugins.loader.cache_loader', version='2.12')
          self._uri     = C.CACHE_PLUGIN_CONNECTION
          self._timeout = float(C.CACHE_PLUGIN_TIMEOUT)
          self._prefix  = C.CACHE_PLUGIN_PREFIX
        ##############################################################
        #### Read default config file
        #### TODO: Add _uri to provide alternate configuration file
        ##############################################################
        #### strip the excption of this file
        cfgFile,ext = os.path.splitext(__file__)
	#### add new INI extention 
        cfgFile    +=".ini"
        display.v("Reading Plugin Config file '%s' " % cfgFile)
        try:
          #### Open the config file
	  fd = open(cfgFile, 'r+')
          #### Read the config file and assign to global varible
	  try:
            cfg = fd.read()
            display.vv("Config Values '%s' " % cfg)
            self._settings = json.loads(cfg)
	  except Exception as e:
            raise AnsibleError('Error Reading config file %s : %s' % cfgFile,to_native(e))
	  finally:
	    fd.close()
        except Exception as e:
	  raise AnsibleError('Error opening %s : %s' % (cfgFile,to_native(e)))
        ####################################################
        #### Initialize Elasticsearch
        ####################################################
        try:
          self.elasticsearch = __import__('elasticsearch')
          self.helpers = __import__('elasticsearch.helpers')
        except ImportError:
          raise AnsibleError('Failed to import elasticsearch module. Maybe you can use pip to install! %s' % to_native(e))
        #####################################################
        #### Initialize _cache file
        #####################################################
        self._cache = {}
        #####################################################
        #### Create connection to the elasticsearch cluster
        #####################################################
        self.es = self._connect()
        self._esping()

    #########################################################
    #### Connect to Elasticsearch cluster
    #########################################################
    def _connect(self):
        try:
          return self.elasticsearch.Elasticsearch(self._settings['es_hostnames'], port=self._settings['es_port'])
        except Exception as e: 
          raise AnsibleError('Failed to connect to elasticsearch %s %s %s' % 
				(self._settings['es_hostnames'], 
				 self._settings['es_port'],
				 to_native(e)))
	return _esping()

    #########################################################
    #### ping Elasticsearch cluster
    #########################################################
    def _esping(self):
        if self.es.ping():
           return True
        display.error('failed to ping host %s %s' % 
                            ( self._settings['es_hostnames'], 
                              self._settings['es_port']))
        return False

    #########################################################
    ####  Get Cache from local file or Elasticsearch cluster
    #########################################################
    def get(self, key):
        #########################################################
        #### OFFLINE Read from file  
        #########################################################
        if self._settings['read_local_cache_directory']:
		cachefile = self._settings['local_cache_directory']+"/"+key 
		display.v("Skipping elasticserch read")
		display.v("read_local_cache_directory: reading local file %s" % cachefile)
		try:
		  fd = open(cachefile, 'r+')
		  try:
		    js = fd.read()
		    self._cache[key] = json.loads(js)
		  except Exception as e:
		    display.error("Error reading cachefile %s : %s" % 
				   (cachefile,
				    to_native(e.message)))
		  finally:
		    fd.close()
		except Exception as e:
		  display.vvv("Error opening cachefile %s " % ( cachefile ))
        else:
          #######################################################
          #### Read from Elasticsearch cluster
          #########################################################
	  if self._esping():
	    try:
	      res = self.es.get(
		    index=self._settings['es_index'], 
		    doc_type='_doc', 
		    id=key)
	      self._cache[key] = res['_source']
	    except Exception as e:
	      display.v("Error getting doc from Elasticsearch %s %s" % ( to_native(e), to_native(res)))
	display.v(to_native(self._cache.get(key)));
	return self._cache.get(key)

    #########################################################
    ####  SET Cache  local file and Elasticsearch cluster
    #########################################################
    def set(self, key, value):
       #########################################################
       ####  deep Get Attribute: process  dot notation 
       #########################################################
        def deepgetattr(obj, attr):
          keys = attr.split('.')
          return functools.reduce(lambda d, key: d.get(key) if d else None, keys, obj)

       #########################################################
       ####  deep Set Attribute: process  dot notation 
       #########################################################
        def deepsetattr(attr, val):
          obj={}
          if attr:
            a = attr.pop(0)
            obj[a] = deepsetattr(attr,val)
            return obj
          return val

        #############################################
	#### Unfiltered values json string
        #############################################
	js = json.dumps(value, cls= AnsibleJSONEncoder, sort_keys=True, indent=4)
        #############################################
        ### Wite Unfiltered data to local cache file
        #############################################
        if "local_cache_directory" in self._settings:
          #write_local_cache_directory  is assumed not sure why you would turn it off if you set a cache directory
          display.vvv("writing to file %s" % self._settings['local_cache_directory']+"/"+key )
          try:
            ### If path does not exist make it
            if not os.path.exists(self._settings['local_cache_directory']):
                   os.makedirs(self._settings['local_cache_directory'],0755)
            ### Open cache file key should be the hostname from inventory
	    fd = open(self._settings['local_cache_directory']+"/"+key, 'w')
	    ### Write unfiltered data to cache file
	    try:
              fd.write(js)
	    except Exception as e:
	      raise AnsibleError("Error writing date to file  %s with error %s" % 
                         ( self._settings['local_cache_directory']+"/"+key,
                           to_native(e)))
	    finally:
	      fd.close()
	  except Exception as e:
	    raise AnsibleError("Error opening file for writing %s with error %s" % 
                         ( self._settings['local_cache_directory']+"/"+key,
                           to_native(e)))
        else:
            display.vvv("local_cache_directory not set skipping")
	#########################################################
        ### Filter Cache data and send to Elasticsearch
        #########################################################
        if self._esping():
	  filter_val={}
          ### Filter fields
	  for ff in self._settings['field_filter']:
	    attr = ff.split('.')
	    a = attr.pop(0)
	    filter_val[a] = deepsetattr(attr,deepgetattr(value,ff))

	  ### Convert the object json string
	  jd = json.dumps(filter_val, cls=AnsibleJSONEncoder, sort_keys=True, indent=4)
	  ########################################################
          #%## Send json to Elasticsearch
	  ########################################################
          try:
            display.vvv("Elasticsearch insert document id='%s' doc = '%s' " % ( value['ansible_hostname'] , jd ))
            result = self.es.index(
			index=self._settings['es_index'], 
			id=value['ansible_hostname'], 
			body=jd, doc_type = "_doc" )
            if result:
	      display.vvv("Results %s" % json.dumps(result))
              return True
	    else:
              display.error("Results %s" % json.dumps(result))
          except Exception as e:
            raise AnsibleError('Error failed to insert data to elasticsearch %s' % to_native(e))
        return False

    #########################################################
    ####  get the key for all caching objects
    #########################################################
    def keys(self):
	display.v("in keys function %s" % json.dumps(self));
        return self._cache.keys()

    #########################################################
    ####  Is there a Cacheable object available
    #########################################################
    def contains(self, key):
        #####################################################
        #### TODO: Search Elasticsearch index 
        #####################################################
        containsFileCache = ("local_cache_directory" in self._settings 
                and os.path.exists("%s/%s" % (self._settings['local_cache_directory'],key)))
	display.vvv("contains function return value %s" % containsFileCache )
        return containsFileCache

    #########################################################
    ####  Delete cacheable object
    #########################################################
    def delete(self, key):
        #### Delete from memory cache
        try:
          del self._cache[key]
        except KeyError:
          pass
        ###########################
        #### Felete from File cache
        ###########################
        try:
          os.remove("%s/%s" % (self._settings['local_cache_directory'], key))
        except (OSError, IOError):
          pass  

	try:
          if self._esping():
	     res = self.es.delete( index=self._settings['es_index'], doc_type="_doc", id=key)
	     #display.v("display result %s "% to_native(res))
             
	except Exception as e:
	  raise AnsibleError('Error delete document from elasticsearch %s : %s' % ( key, to_native(e)))
	pass
    #########################################################
    ####  flush cacheable objects: Wipe all cache values
    #########################################################
    def flush(self):
	display.error("flush function not fully implemented");
        #TODO: need to flush from Elasticsearch
        for key in self._cache.keys():
          self.delete(key)
        self._cache = {}

    #########################################################
    ####  copy cacheable objects
    #########################################################
    def copy(self):
        #TODO: need to flush from Elasticsearch
	display.error("copy function not fully implemented");
        ret = dict()
        for key in self.keys():
            ret[key] = self.get(key)
        return ret
