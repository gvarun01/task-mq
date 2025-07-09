from setuptools import setup, find_packages

setup(
    name="taskforge",
    version="0.1.0",
    description="A robust Python task queue with CLI and API.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "prometheus_client",
        "python-jose",
        "click",
        # sqlite3 is part of the Python standard library
    ],
    entry_points={
        "console_scripts": [
            "taskforge = taskforge.cli:main"
        ]
    },
    include_package_data=True,
    python_requires=">=3.8",
) 