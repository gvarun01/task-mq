from setuptools import setup, find_packages

setup(
    name="task-mq",
    version="0.1.0",
    description="A robust Python task queue with CLI and API.",
    author="Varun Gupta",
    author_email="varungupta8976@gmail.com",
    url="https://github.com/gvarun01/task-mq",
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
            "task-mq = taskmq.cli:main"
        ]
    },
    include_package_data=True,
    python_requires=">=3.8",
) 
