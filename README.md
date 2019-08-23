# STILL WORKING ON THIS, EXPECT MAJOR Changes
Write all Ansible Cache-able variables to Elasticsearch

Here is a basic ansible.cfg which set the Elasticsearch URI  which includes. The Index name to write the data to, and filter what varibles are sent.


```
[defaults]
cache_plugins      = /usr/share/ansible/plugins/cache:{{CWD}}/plugins/cache
stdout_callback=debug
fact_caching = elasticsearch
fact_caching_connection = "http://<ES DNS>:<PORT>/?index=ansible_cache&field_filter=ansible_hostname,ansible_distribution,ansible_distribution_version,ansible_architecture,ansible_product_serial,ansible_product_name,ansible_kernel,ansible_memtotal_mb,ansible_processor,ansible_processor_cores,ansible_processor_count,ansible_processor_vcpus,ansible_local,ansible_vmware,ansible_date_time"

```
