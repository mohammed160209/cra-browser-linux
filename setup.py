from setuptools import setup, find_packages

setup(
    name="cra-browser",
    version="0.1.0",
    description="Native GTK4 and Libadwaita port of the open-source Cra/Arc browser for Arch Linux and CachyOS",
    author="icesaviour / mohammed160209",
    url="https://github.com/mohammed160209/cra-browser-linux",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "cra-browser = cra_browser.app:main",
        ],
    },
    data_files=[
        ("share/applications", ["data/app.crabrowser.Cra.desktop"]),
        ("share/metainfo", ["data/app.crabrowser.Cra.metainfo.xml"]),
        ("share/icons/hicolor/scalable/apps", ["data/app.crabrowser.Cra.svg"]),
        ("share/cra-browser/blocklist", ["data/blocklist/domains.txt"]),
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    python_requires=">=3.10",
)
