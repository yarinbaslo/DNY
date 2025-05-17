from setuptools import setup, find_packages

setup(
    name="dns-forwarder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "psutil",  # For Windows network interface detection
        "requests",  # For content checking
        "openai",  # For AI-based domain analysis
        "beautifulsoup4",  # For better HTML parsing
        "urllib3",  # For retry mechanism
    ],
    python_requires=">=3.6",
) 