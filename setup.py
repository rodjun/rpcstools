from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


with open(path.join(here, 'LICENSE'), encoding='utf-8') as f:
    license_text = f.read()

setup(
    name='rpcstools',
    version='0.1.0',
    description='Simple tool for rpcs3 that can update games and the emulator itself.',
    long_description=long_description,
    author='Rodrigo Junger',
    author_email='rodrigojunger@id.uff.br',
    url='https://github.com/rodjun/rpcstools',
    download_url="https://github.com/rodjun/rpcstools/archive/0.1.tar.gz",
    license=license_text,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords='rpcs3 emulator ps3 sfo development',
    install_requires=['requests',
                      'pyyaml',
                      'tqdm',
                      'urllib3'],
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={
        'console_scripts': ['update-rpcs3-games=rpcstools.rpcstools:update_games']
    }
)
