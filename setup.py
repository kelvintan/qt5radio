#!/usr/bin/env python3

from setuptools import setup, find_packages

# References on writing setup.py
# http://www.siafoo.net/article/77
# http://peak.telecommunity.com/DevCenter/setuptools

setup(name='qt5radio',
      version='0.1',
      description='Online radio station player',
      author='Kelvin Tan',

      scripts=['qt5radio.py'],
      packages=find_packages(),
      data_files=[('icons', ['icons/audio-wave-64.png', 'icons/play-64.png',
                             'icons/stop-64.png', 'icons/downloads-64.png',
                             'icons/mute-64.png'])],
      zip_safe=False,
     )
