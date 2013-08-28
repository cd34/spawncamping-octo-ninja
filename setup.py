import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
try:
    CHANGES = open(os.path.join(here, 'CHANGES.md')).read()
except:
    CHANGES = ''

requires = [
    'boto',
    'webhelpers',
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='ec2bk',
      version='0.0',
      description='ec2bk',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        'Programming Language :: Python',
        ],
      author='',
      author_email='',
      url='',
      keywords='backups ec2 ebs',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='ec2bk',
      install_requires = requires,
      )

