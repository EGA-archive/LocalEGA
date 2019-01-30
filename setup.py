from setuptools import setup
from lega import __version__

setup(name='lega',
      version=__version__,
      url='https://localega.readthedocs.io/',
      license='Apache License 2.0',
      author='EGA System Developers',
      description='Local EGA',
      long_description='''\
LocalEGA ingests into its archive, files that are dropped in some inbox.

The program is divided into several components interconnected via a
message broker and a database.

Users are handled throught Central EGA, directly.
''',
      packages=['lega', 'lega/utils', 'lega/conf'],
      include_package_data=False,
      package_data={'lega': ['conf/loggers/*.yaml', 'conf/defaults.ini']},
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'ega-ingest = lega.ingest:main',
              'ega-verify = lega.verify:main',
              'ega-keyserver = lega.keyserver:main',
              'ega-notifications = lega.notifications:main',
              'ega-finalize = lega.finalize:main',
              'ega-conf = lega.conf.__main__:main',
          ]
      },
      platforms='any',
      )
