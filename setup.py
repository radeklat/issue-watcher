import setuptools

from issuewatcher.constants import __version__, APPLICATION_NAME

DESCRIPTION = (
    "Python test cases watching when an issue is closed and failing a test to "
    "let you know fixed functionality is available."
)

with open("requirements.txt") as fp:
    install_requires = fp.read()

setuptools.setup(
    name=APPLICATION_NAME,
    version=__version__,
    url="https://github.com/radeklat/" + APPLICATION_NAME,
    author="Radek Lat",
    author_email="radek.lat@gmail.com",
    description=DESCRIPTION,
    long_description=(
        "{description}\n\nSee project on GitHub: "
        "https://github.com/radeklat/{app_name}\n\n"
        "Changelog: "
        "https://github.com/radeklat/{app_name}/blob/develop/CHANGELOG.md".format(
            app_name=APPLICATION_NAME, description=DESCRIPTION
        )
    ),
    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing :: Unit",
        "Topic :: System :: Monitoring",
    ],
    license="MIT",
    packages=setuptools.find_packages(exclude=["tests.*"]),
    install_requires=install_requires,
)
