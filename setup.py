from setuptools import setup

setup(
    name='MusicSync',
    version='0.1',
    description='Synchronize music library between devices and folders',
    license="GNU General Public License v3.0",
    url='https://github.com/serpest/MusicSync',
    author='serpest',
    author_email='serpest@protonmail.com',
    packages=['musicsync'],
    install_requires=['mutagen', 'PySide2'],
)
