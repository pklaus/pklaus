# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    import pypandoc
    LDESC = open('README.md', 'r').read()
    LDESC = pypandoc.convert_text(LDESC, 'rst', format='md')
except (ImportError, IOError, RuntimeError) as e:
    print("Could not create long description:")
    print(str(e))
    LDESC = ''

setup(name='pklaus',
      version = '1.0.dev0',
      description = 'Collected Python works of @pklaus',
      long_description = LDESC,
      author = 'Philipp Klaus',
      author_email = 'philipp.l.klaus@web.de',
      url = 'https://github.com/pklaus/pklaus',
      license = 'GPL',
      packages = [
          'pklaus.images.exif',
          'pklaus.images.renaming',
          'pklaus.images.orphans',
          'pklaus.files.name',
          'pklaus.files.removal',
          'pklaus.files.watching',
          'pklaus.epapers.faz',
          'pklaus.epapers.tagesspiegel',
          'pklaus.epapers.onlinekiosk',
          'pklaus.epapers.focus',
          'pklaus.network.ping',
          'pklaus.processes.limit',
          'pklaus.random.identifier',
          'pklaus.python.context_manager',
          ],
      entry_points = {
          'console_scripts': [
              'pklaus.images.renaming.to_exif_datetime = pklaus.images.renaming.to_exif_datetime:cli',
              'pklaus.images.exif.extract = pklaus.images.exif.extract:cli',
              'pklaus.images.exif.fix_datetime = pklaus.images.exif.fix_datetime:main',
              'pklaus.images.orphans.remove = pklaus.images.orphans.remove:main',
              'pklaus.files.watching.tailf = pklaus.files.watching.tailf:main',
              'pklaus.epapers.faz.paperboy = pklaus.epapers.faz.paperboy:main',
              'pklaus.epapers.tagesspiegel.paperboy = pklaus.epapers.tagesspiegel.paperboy:main',
              'pklaus.epapers.onlinekiosk.paperboy = pklaus.epapers.onlinekiosk.paperboy:main',
              'pklaus.epapers.focus.paperboy = pklaus.epapers.focus.paperboy:main',
              'pklaus.network.ping.histogram = pklaus.network.ping.histogram:main',
              'pklaus.processes.limit.timelimit = pklaus.processes.limit.timelimit:main',
              'pklaus.random.identifier.mac = pklaus.random.identifier.mac:main',
          ],
      },
      include_package_data = False,
      zip_safe = True,
      install_requires = [
          "exifread",
          "pillow",
      ],
      keywords = 'pklaus collected works',
      classifiers = [
          'Development Status :: 4 - Beta',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: Scientific/Engineering :: Physics',
          'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
          'Topic :: System :: Hardware :: Hardware Drivers',
      ]
)


