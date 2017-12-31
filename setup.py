import os
import re
from setuptools import setup, find_packages
from codecs import open
from os import path
from ultron.config import VERSION

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Requirements for installation
with open('requirements.txt') as requirements_file:
    install_requirements = requirements_file.read().splitlines()

# specify any extra requirements for installation
extra_requirements = dict()
extra_requirements_dir = 'packaging/requirements'
for extra_requirements_filename in os.listdir(extra_requirements_dir):
    filename_match = re.search(r'^requirements-(\w*).txt$', extra_requirements_filename)
    if filename_match:
        with open(os.path.join(extra_requirements_dir, extra_requirements_filename)) as extra_requirements_file:
            extra_requirements[filename_match.group(1)] = extra_requirements_file.read().splitlines()

setup(
    name='ultron',
    version=VERSION,
    description='Just another infrastructure management tool',
    long_description=long_description,
    url='https://github.com/sayanarijit/ultron',
    download_url='https://github.com/sayanarijit/ultron/archive/{}.tar.gz'.format(VERSION),
    author='Arijit Basu',
    author_email='sayanarijit@gmail.com',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
        'Operating System :: POSIX'
    ],
    keywords='Infrastructure Management Tool',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=install_requirements,
    extras_require=extra_requirements,
    scripts=['bin/ultron-run']
)
