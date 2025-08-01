"""
Setup script for Phoenix Hydra System Review Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(
    encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')

setup(
    name="phoenix-system-review",
    version="1.0.0",
    author="Phoenix Team",
    author_email="team@phoenix.dev",
    description="Comprehensive evaluation framework for Phoenix Hydra system components",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/phoenix/phoenix-system-review",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "mamba": [
            "mamba-ssm>=1.2.0",
            "transformers>=4.36.0",
            "torch>=2.0.0",
            "accelerate>=0.20.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "phoenix-review=phoenix_system_review.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "phoenix_system_review": [
            "templates/*.md",
            "templates/*.html",
            "configs/*.json",
            "configs/*.yaml",
        ],
    },
)
