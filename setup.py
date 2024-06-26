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
    zip_safe=False,
    platforms='any',
    install_requires=[
        'requests-toolbelt==1.0.0',
        'arcsecond>=2.0.4',
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
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
