import re
from setuptools import setup

README = open('README.rst').read()

CHANGES = open('CHANGES.rst').read()

setup(
    name='bdist-venv2',
    version=(
        re
        .compile(r".*__version__ = '(.*?)'", re.S)
        .match(open('bdist_venv2.py').read())
        .group(1)
    ),
    url='http://github.com/bninja/bdist-venv2',
    license='BSD',
    author='me',
    author_email='me@aitmp.com',
    description='Python distutils extension to create virtualenv built distributions.',
    long_description=README + '\n\n' + CHANGES,
    zip_safe=False,
    platforms='any',
    py_modules=['bdist_venv2'],
    install_requires=[
         'virtualenv',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={
        'distutils.commands': [
            'bdist_venv2 = bdist_venv2:bdist_venv2',
        ],
    },
)
