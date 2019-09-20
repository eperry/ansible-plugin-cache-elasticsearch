from setuptools import setup

setup(name='plugins.cache.elasticsearch',
      version='0.1',
      description='Elasticsearch Cache Plugin',
      url='git@github.com:eperry/ansible-plugin-cache-elasticsearch.git',
      author='Edward Perry',
      author_email='edwardperry1@gmail.com',
      packages=['plugins.cache.elasticsearch'],
      install_requires=[
          'elasticsearch',
          'pytz',
          'json',
          'logging',
          'pytz',
          'time',
          'json'
      ],
      zip_safe=False)
