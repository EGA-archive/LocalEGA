from setuptools import setup
from lega import __version__ as lega_version

setup(name='lega',
      version=lega_version,
      url='http://lega.nbis.se',
      license='Apache License 2.0',
      author='NBIS System Development Team',
      author_email='ega@nbis.se',
      description='Local EGA',
      packages=['lega'],
      entry_points={
          'console_scripts': [
              'ega-ingestion = lega.ingestion:main',
              'ega-worker = lega.worker:main',
              'ega-vault = lega.vault:main'
          ]
      },
      platforms = 'any',
      install_requires=[
          'pika==0.10.0',
          'gpg==1.8.0',
          'uWSGI==2.0.14',
          'pycryptodome==3.4.5',
          'Flask==0.12',
      ],
)
