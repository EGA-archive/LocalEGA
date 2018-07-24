from setuptools import setup
from lega import __version__

setup(name='lega',
      version=__version__,
      url='http://lega.nbis.se',
      license='Apache License 2.0',
      author='NBIS System Developers',
      author_email='ega@nbis.se',
      description='Local EGA',
      long_description='''\
LocalEGA ingests into its vault, files that are dropped in some inbox.

The program is divided into several components interconnected via a
message broker and a database.

Users are handled throught Central EGA, directly.
''',
      packages=['lega', 'lega/utils', 'lega/conf'],
      include_package_data=False,
      package_data={ 'lega': ['conf/loggers/*.yaml', 'conf/defaults.ini'] },
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'ega-ingest = lega.ingest:main',
              'ega-inbox = lega.inbox:main',
              'ega-verify = lega.verify:main',
              'ega-keyserver = lega.keyserver:main',
              'ega-conf = lega.conf.__main__:main',
          ]
      },
      platforms = 'any',
      # install_requires=[
      #     'pika==0.11.0',
      #     'colorama==0.3.7',
      #     'psycopg2-binary==2.7.4',
      #     'aiopg'==0.13.0,
      #     'aiohttp==2.3.8',
      #     'aiohttp-jinja2==0.13.0',
      #     'fusepy',
      #     'sphinx_rtd_theme',
      #     'cryptography==2.1.4',
      #     'pgpy',
      #     'boto3',
      #     'git+https://github.com/NBISweden/LocalEGA-cryptor.git',
      # ],
)
