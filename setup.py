"""
 Oort server for managing and uploading all your files to arcsecond.io cloud storage.
"""
import ast
import re

from setuptools import find_packages, setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('oort/__init__.py', 'rb') as f:
    __version__ = str(ast.literal_eval(_version_re.search(f.read().decode('utf-8')).group(1)))

with open("README.md", "r") as f:
    long_description = f.read()

### SETUP ##############################################################################################################

setup(
    name='oort-cloud',
    version=__version__,
    url='https://github.com/arcsecond-io/oort',
    license='MIT',
    author='Cedric Foellmi',
    author_email='cedric@arcsecond.io',
    description="Oort utility to upload all your files in Arcsecond.io's cloud storage.",
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['oort/server/app/static/*', 'oort/server/app/templates/*'],
    },
    zip_safe=False,
    platforms='any',
    install_requires=[
        'arcsecond>=1.2.4',
        'astropy>=4',
        'flask>=1.1',
        'peewee>=3',
        'watchdog>=0.10',
        'supervisor>=4.2',
        'dateparser',
        'python-dotenv'
    ],
    entry_points={
        'console_scripts': [
            'oort = oort.cli.cli:main',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
