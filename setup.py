"""
Setup script for AbirQu — Full-Stack Quantum Computing SDK.
Note: This file is maintained for backward compatibility.
The primary build configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="abirqu",
    version="1.0.0",
    author="Abir Maheshwari",
    author_email="abhirsxn@gmail.com",
    description="Full-stack quantum computing SDK — real hardware support for IBM, D-Wave, SpinQ, and all quantum computers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Abiress/abirqu",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "networkx>=2.6",
        "requests>=2.31.0",
    ],
    extras_require={
        "gpu": ["cupy>=12.0.0"],
        "visualization": ["matplotlib>=3.5.0"],
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
