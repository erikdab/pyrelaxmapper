#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'click>=6.0',
    'nltk>=3.2',
    'configparser>=3.5',
    'colorama>=0.3',        # Required for colors on Windows
    'mysqlclient>=1.3',
    'sqlalchemy>=1.1',

    'numpy>=1.12',
    # 'cairocffi>=0.8',       # python-igraph prerequisite
    # 'python-igraph>=0.7',
]

test_requirements = [
]

setup(
    name='pyrelaxmapper',
    version='0.1.0',
    description="pyrelaxmapper utilizes relaxation mapping to propose mappings between wordnets.",
    long_description=readme + '\n\n' + history,
    author="Erik David Burnell",
    author_email='erik.d.burnell@gmail.com',
    url='https://github.com/erikdab/pyrelaxmapper',
    packages=[
        'pyrelaxmapper',
    ],
    package_dir={'pyrelaxmapper':
                 'pyrelaxmapper'},
    entry_points={
        'console_scripts': [
            'pyrelaxmapper=pyrelaxmapper.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="GNU Lesser General Public License v3",
    zip_safe=False,
    keywords='pyrelaxmapper',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
