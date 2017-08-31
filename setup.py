from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name="usher-heartbeat",
    version="0.1",
    description="register and keep heartbeat for backend app",
    packages=["heartbeat"],
    scripts=[
        "bin/heartbeat",
        "bin/pick_port",
    ],
    install_requires=[
        "pyyaml",
        "requests",
    ],
)
