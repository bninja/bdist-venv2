===========
bdist-venv2
===========

Implements a python distutils ``bdist_venv2`` command for creating a `virtualenv <https://github.com/pypa/virtualenv>`_ 
built distribution.

It was based on what was already done by:

    https://github.com/mgood/bdist_venv
    
but incorporates ideas from:

    https://github.com/spotify/dh-virtualenv
    http://lucumr.pocoo.org/2012/6/22/hate-hate-hate-everywhere

Install
-------

.. code:: bash

    sudo pip install bdist-venv2
    

Example
-------

Say you want to distribute a project called my-project. Get to its `setup.py`:

.. code:: bash

    cd ~/code/my-project/src
    ls
    ...
    setup.py
    ...

Make sure you are *not* in a virtualenv (you can't create a virtualenv from
within a virtualenv). If you in one exit it:

.. code:: bash

    deactivate

You can either create a "relocatable" virtualenv ala `bdist_venv <https://github.com/mgood/bdist_venv>`_:

.. code:: bash

    python setup.py bdist_venv2 -f gztar
    
or one "fixed-up" to be unpacked to a particular location:

.. code:: bash

    python setup.py bdist_venv2 -l /usr/lib/my-package -f gztar

You'll find the results in ``dist`` which might look something like:

.. code:: bash

    ls dist
    ...
    dist/my-package-0.1.0.linux_x86_64-py2.7.tar.gz
    ...

depending on your environment.

Usage
-----

.. code:: bash

    python setup.py bdist_venv2 --help

    Common commands: (see '--help-commands' for more)
    
      setup.py build      will build the package underneath 'build/'
      setup.py install    will install the package
    
    Global options:
      --verbose (-v)  run verbosely (default)
      --quiet (-q)    run quietly (turns verbosity off)
      --dry-run (-n)  don't actually do anything
      --help (-h)     show detailed help message
      --no-user-cfg   ignore pydistutils.cfg in your home directory
    
    Options for 'bdist_venv2' command:
      --bdist-dir (-b)     temporary directory for creating the distribution
      --location-dir (-l)  location where virtualenv will be installed to
                           (default: relocatable)
      --extras (-e)        list of extras to included in the virtualenv
      --plat-name (-p)     platform name to embed in generated filenames (default:
                           linux-x86_64)
      --keep-temp (-k)     keep the installation tree around after creating the
                           distribution
      --keep-compiled      keep compiled files in the distribution
      --dist-name (-n)     name of the built distribution
      --dist-dir (-d)      directory to put final built distributions in
      --format (-f)        archive format to create (tar, ztar, gztar, zip)
                           (default: none)
      --owner (-u)         Owner name used when creating a tar file (default:
                           current user)
      --group (-g)         Group name used when creating a tar file (default:
                           current group)
    
    usage: setup.py [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
       or: setup.py --help [cmd1 cmd2 ...]
       or: setup.py --help-commands
       or: setup.py cmd --help
