from setuptools import setup, find_packages

setup(
    name="hpd-cli-core",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
        "tenacity>=8.0.0",
        "google-genai>=0.3.0",
    ],
    entry_points={
        "console_scripts": [
            "hpd = hpd_cli.cli:main",
        ],
    },
    python_requires=">=3.8",
)
