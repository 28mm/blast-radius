from setuptools import setup
from setuptools import find_packages

setup(
    name='BlastRadius',
    version='0.1.16',
    author='Patrick McMurchie',
    author_email='patrick.mcmurchie@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    scripts=['bin/blast-radius'],
    url='http://pypi.python.org/pypi/BlastRadius/',
    license='LICENSE.txt',
    description='Interactive visualizations of Terraform dependency graphs',
    long_description=open('README.md').read(),
    python_requires='>=3.5.0',
    install_requires=[
        "Flask",
        "jinja2",
        "pyhcl>=0.3.10",
        "requests",
        "BeautifulSoup4"
    ],
)
