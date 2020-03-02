# -*- coding: utf-8 -*-
import re
from setuptools import setup

""" Setup file only used for forkie CLI. Do not run this if you want to install the forkie web repository on
    your system, instead run bin/installforkie.sh
""" 

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('client/forkie.py').read(),
    re.M
).group(1)

# Opening readme
with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")
f.close()

# Opening requirements
with open('requirements_cli.txt') as f:
    requirements = f.read().splitlines()
f.close()

setup(
    name="forkieCLI",
    packages=["client", 'src', 'src.api', 'src.api.files'],
    # package_data={
    #     # If any package contains *.txt or *.rst files, include them:
    #     "": ["__init__.py"],
    # },
    entry_points={"console_scripts": ['forkie = client.forkie:main']},
    version=version,
    python_requires='>=3',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    
    description="The CLI tool for the forkie file versioning system",
    long_description=long_descr,
    long_description_content_type='text/markdown',
    
    author="Jakab Zeller",
    author_email="jakabzeller0@gmail.com",
    url="https://github.com/RHUL-CS-Projects/CS1813_2020_09",
)