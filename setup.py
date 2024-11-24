from setuptools import setup, find_packages
from version import __version__

setup(
    name="diode_vcenter_agent",
    version=__version__,
    description="A vCenter to NetBox agent using the NetBoxLabs Diode SDK.",
    author="Eric Hester",
    author_email="hester1@clemson.edu",
    url="https://github.com/erichester76/diode_vcenter_agent",
    packages=find_packages(),
    install_requires=[
        "diode-sdk-python",
        "pyvmomi",
        "python-dotenv"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "diode-vcenter-agent=main:main",
        ],
    },
)
