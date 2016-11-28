#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""Matplotlib graphs for OpenFisca -- a versatile microsimulation free software"""


from setuptools import setup, find_packages


classifiers = """\
Development Status :: 2 - Pre-Alpha
Environment :: X11 Applications :: Qt
License :: OSI Approved :: GNU Affero General Public License v3
Operating System :: POSIX
Programming Language :: Python
Topic :: Scientific/Engineering :: Information Analysis
"""

doc_lines = __doc__.split('\n')


setup(
    name = 'OpenFisca-Matplotlib',
    version = '0.5b1',

    author = 'OpenFisca Team',
    author_email = 'contact@openfisca.fr',
    classifiers = [classifier for classifier in classifiers.split('\n') if classifier],
    description = doc_lines[0],
    keywords = 'benefit microsimulation social tax',
    license = 'http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    long_description = '\n'.join(doc_lines[2:]),
    url = 'https://github.com/openfisca/openfisca-matplotlib',

    include_package_data = True,
    install_requires = [
        'OpenFisca-France >= 6.0.1',
        ],
    packages = find_packages(),
    message_extractors = {
        'openfisca_matplotlib': [
            ('**.py', 'python', None),
            ],
        },
    zip_safe = False,
    )
