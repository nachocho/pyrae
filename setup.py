import setuptools
from pyrae import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyrae",
    version=__version__,
    author="Javier Treviño",
    author_email="javier.trevino@gmail.com",
    description="Perform searches against the RAE dictionary.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nachocho/pyrae",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
