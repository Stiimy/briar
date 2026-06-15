from setuptools import setup, find_packages

setup(
    name="briar",
    version="0.1.0",
    description="🥀 Autonomous AI Pentester — find vulns before hackers do",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Stiimy",
    url="https://github.com/Stiimy/briar",
    packages=find_packages(),
    install_requires=[
        "requests", "click", "rich", "fastapi", "uvicorn",
        "python-docx", "openpyxl", "python-pptx", "matplotlib", "plotly",
    ],
    entry_points={
        "console_scripts": [
            "briar=briar.cli:cli",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Topic :: Security",
    ],
)
# Black rose didn't do it
