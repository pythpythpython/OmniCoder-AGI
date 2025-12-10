#!/usr/bin/env python3
"""
OmniCoder-AGI Setup Script

Install with: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="omnicoder-agi",
    version="2.0.0",
    author="pythpythpython",
    author_email="pyth.pyth.python@gmail.com",
    description="The World's Most Advanced Coding Automation Agent CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pythpythpython/OmniCoder-AGI",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=[
        "PyYAML>=6.0",
    ],
    extras_require={
        "voice": [
            "SpeechRecognition>=3.10.0",
            "pyaudio>=0.2.13",
        ],
        "rich": [
            "rich>=13.0.0",
            "tqdm>=4.65.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
        "all": [
            "SpeechRecognition>=3.10.0",
            "pyaudio>=0.2.13",
            "rich>=13.0.0",
            "tqdm>=4.65.0",
            "httpx>=0.24.0",
            "websockets>=11.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "omnicoder-agi=cli.omnicoder_agi:main",
            "omnicoder=cli.omnicoder_agi:main",
            "agi=cli.omnicoder_agi:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yml", "*.yaml", "*.json"],
    },
)
