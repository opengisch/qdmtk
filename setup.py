from distutils.core import setup

from setuptools import find_packages, setup

from qdmtk import __version__

setup(
    name="QDMTK",
    version=__version__,
    description="QGIS Datamodel toolkit",
    author="Olivier Dalang",
    author_email="olivier@opengis.ch",
    url="https://github.com/opengisch/qdmtk",
    packages=["qdmtk"],
    packages=find_packages(),
    install_requires=open("requirements.txt", encoding="utf-8").read().splitlines(),
    include_package_data=True,
)
