#!/usr/bin/env python

from distutils.core import setup

version = '0.2'

long_description = """txPachube is a Python wrapper for the v2 Pachube API, based on the Twisted networking framework. Use it to integrate non blocking access to the Pachube API into your Python Twisted application.

It implements the full Pachube API (Feeds, Datastreams, Datapoints, Triggers, Users, Keys) and many of the data structures (Unit, Location, Datapoint, Datastream, Environment, EnvironmentList, Trigger, TriggerList Key, KeyList, User, UserList) contained in requests and responses.

The data structures support encoding and decoding from JSON/XML formats. These structures are useful when building data to send to Pachube and also for processing Pachube data returned from queries.
"""


setup(name='txPachube',
      version=version,
      description='txPachube is a Python wrapper for the v2 Pachube API, based on the Twisted networking framework',
      long_description=long_description,
      author='Chris Laws',
      author_email : 'clawsicus@gmail.com',
      license='http://www.opensource.org/licenses/mit-license.php',
      url='https://github.com/claws/txPachube',
      download_url='https://github.com/claws/txPachube/tarball/master'
      packages=['txPachube'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Framework :: Twisted']
      )




