import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-topopartner',
    version='1.6.0',
    packages=find_packages(),
    include_package_data=True,
    description='A Django app for topographic data management.',
    long_description=README,
    url='https://chalier.fr/topopartner',
    author='Yohan Chalier',
    author_email='yohan@chalier.fr',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        "Django",
        "django-mathfilters",
        "gpxpy",
        "numpy",
        "numpy-stl",
        "requests",
    ],
)
