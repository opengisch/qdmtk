import os
from distutils.core import setup

from setuptools import find_packages, setup

from qdmtk import __version__

requirements_path = os.path.join("qdmtk", "requirements.txt")

setup(
    name="QDMTK",
    version=__version__,
    description="QGIS Datamodel toolkit",
    author="Olivier Dalang",
    author_email="olivier@opengis.ch",
    url="https://github.com/opengisch/qdmtk",
    packages=find_packages(),
    install_requires=open(requirements_path, encoding="utf-8").read().splitlines(),
    include_package_data=True,
)
