from setuptools import setup, find_packages

setup(
    name="dns-forwarder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "psutil",  # For Windows network interface detection
    ],
    python_requires=">=3.6",
) 