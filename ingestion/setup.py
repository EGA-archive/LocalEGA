from setuptools import setup, find_packages

setup(name='lega',
      version='1.1',  # not via loading lega.__version__
      url='https://localega.readthedocs.io/',
      license='Apache License 2.0',
      author='EGA System Developers',
      description='Local EGA',
      long_description='''\
LocalEGA ingests into its archive, files that are dropped in some inbox.

The program is divided into several components interconnected via a
message broker and a database.

Users are handled through Central EGA, directly.
''',
      packages=find_packages(),
      include_package_data=False,
      package_data={'lega': ['conf/loggers/*.yaml']},
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'ega-ingest = lega.ingest:main',
              'ega-verify = lega.verify:main',
              'ega-finalize = lega.finalize:main',
              'ega-conf = lega.conf.__main__:main',
          ]
      },
      platforms='any',
      install_requires=[
          'amqpstorm',
          'requests',
          'psycopg2-binary>=2.8.5',
          'PyYaml',
          'boto3',
          'crypt4gh>=1.3',
      ])
