from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name="usher_heartbeat",
    version="0.1.0",
    description="register and keep heartbeat for backend app",
    keywords="guokr gateway usher register heartbeat",
    packages=["heartbeat"],
    install_requires=[
        "pyyaml",
        "requests",
    ],
    scripts=[
        "bin/heartbeat",
        "bin/pick_port",
    ],
)
