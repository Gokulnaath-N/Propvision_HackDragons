from setuptools import setup, find_packages
from pathlib import Path

# Provide path to this directory
this_directory = Path(__file__).parent

# Read long description from README.md
readme_path = this_directory / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")
else:
    long_description = ""

# Read install_requires from requirements.txt
requirements_path = this_directory / "requirements.txt"
install_requires = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                install_requires.append(line)

setup(
    name="propvision-ai",
    version="0.1.0",
    author="placeholder",
    description="AI-powered property image intelligence platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.11",
    packages=find_packages(where="."),
    install_requires=install_requires,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.0.0"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
