from setuptools import setup

README = open('README.rst').read()

CHANGES = open('CHANGES.rst').read()

setup(
    name='bdist-venv2',
    version='0.1.0',
    url='http://github.com/bninja/bdist-venv2',
    license='BSD',
    author='No One',
    author_email='noone@nowhere.org',
    description='Python distutils extension to create virtualenv built distributions.',
    long_description=README + '\n\n' + CHANGES,
    zip_safe=False,
    platforms='any',
    py_modules=['bdist_venv2'],
    install_requires=[
#         'virtualenv',
    ],
    extras_require={
        'kazoo':  'kazoo >=1.3.1',
        'newrelic': 'newrelic >=1.13.1.31',
    },
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
