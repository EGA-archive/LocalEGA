from setuptools import setup
from lega import __version__

setup(name='lega',
      version=__version__,
      license='Apache License 2.0',
      author='EGA System Developers',
      author_email='all.ega@crg.eu',
      description='Local EGA',
      long_description='''\
LocalEGA ingests into its vault, files that are dropped in some inbox.

The program is divided into several components interconnected via a
message broker and a database.

Users are handled through Central EGA, directly.
''',
      packages=['lega', 'lega/utils', 'lega/conf'],
      include_package_data=False,
      package_data={'lega': ['conf/loggers/*.yaml']},
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'lega-ingest    = lega.ingest:main',
              'lega-verify    = lega.verify:main',
              'lega-finalize  = lega.finalize:main',
              'lega-notifier  = lega.notifications:main',
              'lega-outgest   = lega.outgest:main',
              'lega-streamer  = lega.streamer:main',
              'lega-index     = lega.index:main',
              # 'lega-cleanup   = lega.cleanup:main',
          ]
      },
      platforms='any',
      )
