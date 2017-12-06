from setuptools import setup
from lega import __version__
from markdown import markdown
from pathlib import Path

def readme():
    with open(Path(__file__).parent / 'README.md') as f:
        return markdown(f.read())

setup(name='lega',
      version=__version__,
      url='http://lega.nbis.se',
      license='Apache License 2.0',
      author='NBIS System Developers',
      author_email='ega@nbis.se',
      description='Local EGA',
      long_description=readme(),
      packages=['lega', 'lega/utils', 'lega/conf'],
      include_package_data=False,
      package_data={ 'lega': ['conf/loggers/*.yaml', 'conf/defaults.ini', 'conf/templates/*.html'] },
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'ega-frontend = lega.frontend:main',
              'ega-ingest = lega.ingest:main',
              'ega-vault = lega.vault:main',
              'ega-verify = lega.verify:main',
              'ega-monitor = lega.monitor:main',
              'ega-keyserver = lega.keyserver:main',
              'ega-conf = lega.conf.__main__:main',
              'ega-socket-proxy = lega.utils.socket:proxy',
              'ega-socket-forwarder = lega.utils.socket:forward',
          ]
      },
      platforms = 'any',
      install_requires=[
          'pika==0.11.0',
          'aiohttp==2.2.5',
          'pycryptodomex==3.4.7',
          'aiopg==0.13.0',
          'colorama==0.3.7',
          'aiohttp-jinja2==0.13.0',
      ],
)
