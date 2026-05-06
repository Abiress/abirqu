"""
Setup script for AbirQu — Next-Generation Quantum Computing Library.
"""

from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="abirqu",
    version="0.1.0",
    author="Abir Maheshwari",
    author_email="abir@example.com",
    description="Next-generation quantum computing SDK with LDPC codes and post-quantum security",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abirqu/abirqu",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "networkx>=2.6",
    ],
    extras_require={
        "gpu": ["cupy>=12.0.0"],
        "visualization": ["matplotlib>=3.5.0", "d3js>=3.0.0"],
        "crypto": ["cryptography>=3.4.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "hypothesis>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "abirqu=abirqu.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "abirqu": ["py.typed"],
    },
)
