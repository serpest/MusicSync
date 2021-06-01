from setuptools import setup, find_packages

setup(
    name='MusicSync',
    version='0.2',
    description='Synchronize music library between devices and folders',
    license="GNU General Public License v3.0",
    url='https://github.com/serpest/MusicSync',
    author='serpest',
    author_email='serpest@protonmail.com',
    packages=find_packages(),
    install_requires=['mutagen', 'pydub', 'PySide2'],
)
