from setuptools import setup
from lega import __version__ as lega_version
from markdown import markdown
from pathlib import Path

def readme():
    with open(Path(__file__).parent / 'README.md') as f:
        return markdown(f.read())

setup(name='lega',
      version=lega_version,
      url='http://lega.nbis.se',
      license='Apache License 2.0',
      author='NBIS System Developers',
      author_email='ega@nbis.se',
      description='Local EGA',
      long_description=readme(),
      packages=['lega'],
      include_package_data=True,
      zip_safe=True,
      entry_points={
          'console_scripts': [
              'ega-frontend = lega.frontend:main',
              'ega-worker = lega.worker:main',
              'ega-vault = lega.vault:main',
              'ega-verify = lega.verify:main',
              'ega-monitor = lega.monitor:main',
              'ega-publisher = lega.cega_publisher:main',
              'ega-connect = lega.connect:main',
              'ega-conf = lega.__main__:main',
          ]
      },
      platforms = 'any',
      install_requires=[
          'pika==0.10.0',
          'aiohttp==2.0.5',
          'pycryptodomex==3.4.5',
          'aiopg==0.13.0',
          'aioamqp==0.10.0',
          'colorama==0.3.7',
          'aiohttp-swaggerify==0.1.0',
          #'jinja2==2.6.5',
          'aiohttp-jinja2==0.13.0',
          'aiohttp-cors==0.5.2',
          #'Markdown==2.6.8',
      ],
)
