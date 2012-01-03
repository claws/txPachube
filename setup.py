#!/usr/bin/env python

sdict = {
    'name' : 'txpachube',
    'version' : '0.1',
    'description' : 'Python/Twisted wrapper of Pachube API',
    'author' : 'Chris Laws',
    'author_email' : 'clawsicus@gmail.com',
    'url' : 'https://github.com/claws/txPachube',
    'packages' : ['txPachube'],
    'classifiers' : [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Twisted',
        ],
}

from setuptools import setup
setup(**sdict)
