import codecs
import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

with open(os.path.join(here, "youtube_client", "version.py")) as fp:
    exec(fp.read())

setup(
    name="youtube_client",
    version=__version__,  # noqa: F821
    author="warm3301",
    packages=["youtube_client"],
    package_data={"": ["LICENSE"]},
    license="The Unlicense (Unlicense)",
    description=("Python 3 library for downloading YouTube Videos."),
    include_package_data=True,
    long_description_content_type="text/markdown",
    long_description=long_description,
    zip_safe=True,
    python_requires=">=3.7",
    keywords=["youtube", "download", "video", "stream",],
)
