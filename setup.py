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
          'pklaus.files.name',
          ],
      entry_points = {
          'console_scripts': [
              'pklaus.images.renaming.to_exif_datetime = pklaus.images.renaming.to_exif_datetime:cli',
              'pklaus.images.exif.extract = pklaus.images.exif.extract:cli',
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


