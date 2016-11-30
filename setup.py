#! /usr/bin/env python3
from setuptools import setup
from setuptools import find_packages

import netsyslog


setup(
    py_modules=['netsyslog'],
    name='py3-netsyslog',
    version=netsyslog.__version__,
    description="Send log messages to remote syslog servers.",
    long_description=open('README.rst').read(),
    url='https://github.com/sleepy771/py3-netsyslog',

    author='Filip Hornak',
    author_email='sleepy771@gmail.com',

    classifiers=[
        "Development Status :: 3 - Alpha",
        'Intended Audience :: Developers',

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",

        "Topic :: System :: Networking",
        "Topic :: System :: Networking :: Monitoring",

    ],
    zip_safe=False,
    include_package_data=True,
    install_requires=open("requirements.txt").read().splitlines(),

    test_suite='py.test',
    tests_require=["pytest"],
    extras_require={
         "test": [
             "pytest",
         ],
    #     "docs": [
    #         "sphinx",
    #         "sphinxcontrib-napoleon",
    #     ]
    },
)
