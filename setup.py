#!/usr/bin/python
from setuptools import setup

setup(
    name='vse-viprlogger',
    version='1.0',
    packages=['viprlogger'],
    package_data={
        #If any package contains *.py or *.json files, include them:
        'viprlogger': ['*.json'],
    },
    url='',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[

        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Customer Service',
        'Topic :: Software Development :: Libraries :: Application Frameworks',

        # Pick your license as you wish (should match "license" above)
        'License :: Other/Proprietary License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.

        'Programming Language :: Python :: 2.7.5',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    license='EMC Corp',
    description='ViPR Log Manager'
)
