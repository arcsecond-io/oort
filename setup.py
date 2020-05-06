"""
 Oort server for managing and uploading all your files to arcsecond.io cloud storage.
"""
import ast
import re

from setuptools import find_packages, setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('oort/__init__.py', 'rb') as f:
    __version__ = str(ast.literal_eval(_version_re.search(f.read().decode('utf-8')).group(1)))

setup(
    name='oort-cloud',
    version=__version__,
    url='https://github.com/arcsecond-io/oort',
    license='MIT',
    author='Cedric Foellmi',
    author_email='cedric@arcsecond.io',
    description='Oort server to manage all your files in arcsecond.io cloud.',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['oort/app/static/*', 'oort/app/templates/*'],
    },
    zip_safe=False,
    platforms='any',
    install_requires=[
        'flask',
        'arcsecond>=0.9.6',
        'astropy',
        'dateparser',
        'python-dotenv'
    ],
    entry_points={
        'console_scripts': [
            'oort = oort.cli:main',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
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
