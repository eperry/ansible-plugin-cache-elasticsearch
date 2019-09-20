# STILL WORKING ON THIS, EXPECT MAJOR Changes
Write "Filteredlist of" any Ansible Cache-able variables to Elasticsearch
Reading has not been implemented yet.


{{CWD}}/plugins/cache/elasticsearch.py = plugin to write selected ansible varibles to elasticsearch
{{CWD}}/plugins/cache/elasticsearch.ini = Configuration File for the plugin
{{CWD}}/kibana-canvas.json = a default system canvas that reads ansible_cache index and gives you a summary.

![Canvas](https://github.com/eperry/ansible-plugin-cache-elasticsearch/raw/master/images/Canvas.png)

![Json](https://github.com/eperry/ansible-plugin-cache-elasticsearch/raw/master/images/json.png)

Here is a basic ansible.cfg which set the Elasticsearch URI  which includes. The Index name to write the data to, and filter what varibles are sent.


```
[defaults]
cache_plugins      = /usr/share/ansible/plugins/cache:{{CWD}}/plugins/cache
stdout_callback=debug
fact_caching = elasticsearch
```

If field_filter is not passed as an argument then use these default values
```
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
"ansible_date_time"
```
