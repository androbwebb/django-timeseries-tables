import os
from setuptools import setup, find_packages


def long_desc(root_path):
    FILES = ['README.rst']
    for filename in FILES:
        filepath = os.path.realpath(os.path.join(root_path, filename))
        if os.path.isfile(filepath):
            with open(filepath, mode='r') as f:
                yield f.read()


HERE = os.path.abspath(os.path.dirname(__file__))
long_description = "\n\n".join(long_desc(HERE))


def get_version(root_path):
    with open(os.path.join(root_path, 'django_timeseries_tables', '__init__.py')) as f:
        for line in f:
            if line.startswith('__version__ ='):
                return line.split('=')[1].strip().strip('"\'')


setup(
    name='django-timeseries-tables',
    version=get_version(HERE),
    license="BSD",
    description='Django timeseries models',
    long_description=long_description,
    author='Andrew Webb',
    author_email='androbwebb@gmail.com',
    maintainer='AndRobWebb',
    url='https://github.com/androbwebb/django-timeseries-tables/',
    packages=find_packages(exclude=['tests*']),
    install_requires=['Django>=1.8'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
    ],
    zip_safe=False,
    tests_require=['Django>=1.8'],
    package_data={
        'model_utils': [
            'locale/*/LC_MESSAGES/django.po', 'locale/*/LC_MESSAGES/django.mo'
        ],
    },
)
