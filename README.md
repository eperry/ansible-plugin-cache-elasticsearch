# It works well

* TODO: delete elasticsearch
* TODO: flush elasticsearch
* COMPLETE: Get from Elasticsearch
* COMPLETE: Set elasticsearch
* COMPLETE: Local File cache option 

# Files defined 
{{CWD}}/plugins/cache/elasticsearch.py  = plugin to write selected ansible varibles to elasticsearch

{{CWD}}/plugins/cache/elasticsearch.ini = Configuration File for the plugin

{{CWD}}/kibana-canvas.json   = a default system canvas that reads ansible_cache index and gives you a summary.

{{CWD}}/install-playbook.yml = install the prerequisites

{{CWD}}/debug-playbook.yml   = test examples playbook


# Installation

There is one dependency and makes a copy of the ansible.cfg.example to asnible.cfg (For now)

```
ansible-playbook install-playbook.yml --ask-become-pass
```

# Kibana Canvas
![Canvas](https://github.com/eperry/ansible-plugin-cache-elasticsearch/raw/master/images/Canvas.png)


# Viewing the json in Kibana
![Json](https://github.com/eperry/ansible-plugin-cache-elasticsearch/raw/master/images/json.png)

Here is a basic ansible.cfg which set the Elasticsearch URI  which includes. The Index name to write the data to, and filter what varibles are sent.

# Configuration Ansible

```
[defaults]
cache_plugins      = /usr/share/ansible/plugins/cache:{{CWD}}/plugins/cache
stdout_callback=debug
fact_caching = elasticsearch
```

# Configration Elasticsarch.ini

The Elasticearch.ini is expected to be in the same location as Elasticsearch.py

{{CWD}}/plugins/cache/eleasticsearch.ini
This is JSON format because it was quick and easy for me. 

```
{
"######": "List of hostnames",
"es_hostnames": ["localhost"],
"######": "Elastic Search Port number",
"es_port": 9200,
"######": "Elastic Search Index to save data",
"es_index": "ansible_cache",
"######": "directory name, if unset will disable local cache - relative to {{CWD}} or specify full path",
"local_cache_directory": "ansible_cache",
"######": "Write data to local cache",
"write_local_cache_directory": true,
"######": "Read from local cache instead of elasticsearch good for offline testing",
"read_local_cache_directory": true,
"######": "Filter fields because ansible has many thousands of varibles which we don't need",
"field_filter": [
                    "######": "All fields are optional",
                    "ansible_hostname",
                    "ansible_distribution",
                    "ansible_distribution_version",
                    "ansible_architecture",
                    "ansible_product_serial",
                    "ansible_product_name",
                    "ansible_kernel",
                    "ansible_memtotal_mb",
                    "ansible_processor",
                    "ansible_processor_cores",
                    "ansible_processor_count",
                    "ansible_processor_vcpus",
                    "######": "I even support BASIC DOT notitation to only grab certain sub-fields",
                    "ansible_date_time.iso8601_basic"
                ]
}
```


