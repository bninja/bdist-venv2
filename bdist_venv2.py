"""
Implements the Distutils 'bdist_venv2' command to create a "virtualenv" built
distribution by doing roughly what:

    https://github.com/mgood/bdist_venv
    
does, but incorporates ideas from:

    https://github.com/spotify/dh-virtualenv
    http://lucumr.pocoo.org/2012/6/22/hate-hate-hate-everywhere

You can either create a relocatable "virtualenv" ala bdist_venv like so:

    python setup.py bdist_venv2 -f gztar
    
Or one "fixed-up" to be unpacked to a particular location:

    python setup.py bdist_venv2 -l /usr/lib/my-package -f gztar

You'll find the results in:
    
    dist/my-package-{version}.{platform}-py{python-version}.tar.gz
    
which might be e.g.:

    dist/my-package-0.1.0.linux_x86_64-py2.7.tar.gz
    
depending on your environment.
"""

import marshal
import os
import re
import types

from distutils import log
from distutils.core import Command
from distutils.dir_util import copy_tree, remove_tree, ensure_relative
from distutils.sysconfig import get_python_version
from distutils.util import get_platform

import virtualenv
from distutils.log import Log


__version__ = '0.1.3'


class bdist_venv2(Command):
    
    description = 'create a "virtualenv" distribution'

    user_options = [
        ('bdist-dir=', 'b',
         "temporary directory for creating the distribution"),
        ('location-dir=', 'l',
         "location where virtualenv will be installed to "
         "(default: relocatable)"),
        ('extras=', 'e',
         "list of extras to included in the virtualenv"),
        ('plat-name=', 'p',
         "platform name to embed in generated filenames "
         "(default: %s)" % get_platform()),
        ('keep-temp', 'k',
         "keep the installation tree around after creating the distribution"),
        ('keep-compiled', None,
         "keep compiled files in the distribution"),
        ('dist-name=', 'n',
         "name of the built distribution"),
        ('dist-dir=', 'd',
         "directory to put final built distributions in"),
        ('format=', 'f',
         "archive format to create (tar, ztar, gztar, zip) (default: none)"),
        ('owner=', 'u',
         "Owner name used when creating a tar file (default: current user)"),
        ('group=', 'g',
         "Group name used when creating a tar file (default: current group)"),
    ]
    
    boolean_options = [
        'keep-temp',
        'keep-compiled',
    ]

    def initialize_options (self):
        self.bdist_dir = None
        self.location_dir = None
        self.plat_name = None
        self.keep_temp = 0
        self.keep_compiled = 0
        self.dist_dir = None
        self.dist_name = None
        self.format = None
        self.owner = None
        self.group = None
        self.extras = None


    def finalize_options(self):
        if self.bdist_dir is None:
            bdist_base = self.get_finalized_command('bdist').bdist_base
            self.bdist_dir = os.path.join(bdist_base, 'venv')

        if self.location_dir:
            self.location_dir = ensure_relative(self.location_dir)
            
        if self.extras:
            self.ensure_string_list('extras')

        self.set_undefined_options(
            'bdist',
            ('dist_dir', 'dist_dir'),
            ('plat_name', 'plat_name'),
        )
            
        if self.dist_name is None:
            self.dist_name = '%s.%s-py%s' % (
                self.distribution.get_fullname(),
                self.plat_name,
                get_python_version()
            )

    def run(self):
        # create it
        venv_dir = self.bdist_dir
        if self.location_dir:
            venv_dir = os.path.join(venv_dir, self.location_dir)
        log.info('creating virtualenv "%s"', venv_dir)
        virtualenv.create_environment(venv_dir, clear=True)
         
        # install to
        log.info('installing to virtualenv "%s"', venv_dir)
        pip = os.path.join(venv_dir, 'bin', 'pip')
        install_cmd = [pip, 'install', '.']
        self.spawn(install_cmd)
        if self.extras:
            log.info('installing extras to virtualenv "%s"', venv_dir)
            install_cmd = [pip, 'install']
            for extra in self.extras:
                extras_require = self.distribution.extras_require[extra]
                if isinstance(extras_require, basestring):
                    extras_require = [extras_require] 
                install_cmd.extend(extras_require)
            self.spawn(install_cmd)
        
        # location
        if self.location_dir:
            log.info('making virtualenv "%s" installable to "%s"', venv_dir, self.location_dir)
            self.fixup_shebangs(venv_dir)
            self.fixup_virtual_envs(venv_dir)
            self.fixup_links(venv_dir)
            if self.keep_compiled:
                self.fixup_compiled(venv_dir)
            else:
                self.remove_compiled(venv_dir)
        else:
            log.info('making virtualenv "%s" relocatable', venv_dir)
            virtualenv.make_environment_relocatable(venv_dir)
            self.remove_compiled(venv_dir)

        # distribution        
        dist_root = os.path.join(self.dist_dir, self.dist_name) 
        if self.format:
            # as archive
            archive = self.make_archive(
                dist_root,
                self.format,
                root_dir=self.bdist_dir,
                owner=self.owner,
                group=self.group,
            )
            self.distribution.dist_files.append(
                ('bdist_venv', get_python_version(), archive)
            )
        else:
            # as directory
            copy_tree(self.bdist_dir, dist_root, preserve_symlinks=1)
            self.distribution.dist_files.append(
                ('bdist_venv', get_python_version(), dist_root)
            )

        # cleanup
        if not self.keep_temp:
            remove_tree(self.bdist_dir, dry_run=self.dry_run)

    def fixup_shebangs(self, venv_dir):
        shebang_prefix = '#!' + os.path.abspath(self.bdist_dir)
        bin_dir = os.path.join(venv_dir, 'bin')
        for bin_file in os.listdir(bin_dir):
            bin_file = os.path.join(bin_dir, bin_file)
            if not os.path.isfile(bin_file):
                continue
            lines = open(bin_file, 'rb').readlines()
            if not lines or not lines[0].startswith(shebang_prefix):
                continue
            shebang = '#!' + lines[0][len(shebang_prefix):] 
            log.info('collapse %s shebang "%s"', bin_file, shebang.rstrip())
            lines[0] = shebang
            open(bin_file, 'wb').writelines(lines)
    
    def fixup_virtual_envs(self, venv_dir):
        prefix = os.path.abspath(self.bdist_dir)
        virtual_env_re = re.compile(r'VIRTUAL_ENV\s*(\s+|\=)\s*\"(.+)\"')
        bin_dir = os.path.join(venv_dir, 'bin')
        for bin_file in os.listdir(bin_dir):
            bin_file = os.path.join(bin_dir, bin_file)
            if not os.path.isfile(bin_file):
                continue
            lines = open(bin_file, 'rb').readlines()
            fixups = 0
            for i, line in enumerate(lines):
                m = virtual_env_re.search(line)
                if not m:
                    continue
                virtual_env = line[m.start(2):m.end(2)]
                if not virtual_env.startswith(prefix):
                    continue
                line = line[:m.start(2)] + virtual_env[len(prefix):] + line[m.end(2):]
                log.info('collapse %s VIRTUAL_ENV "%s"', bin_file, line.rstrip())
                lines[i] = line
                fixups += 1
            if not fixups:
                continue
            open(bin_file, 'wb').writelines(lines)
    
    def fixup_compiled(self, venv_dir):
        prefix = os.path.abspath(self.bdist_dir)
        venv_dir = os.path.abspath(venv_dir)
        for dir_path, dir_names, file_names in os.walk(venv_dir):
            for file_name in file_names:
                if not file_name.endswith('pyc'):
                    continue
                file_path = os.path.join(dir_path, file_name)

                # load
                fo = open(file_path, 'rb')
                magic = fo.read(4)
                moddate = fo.read(4)
                code = marshal.load(fo) 
                fo.close()

                # fixup
                code, count = self.fixup_code(code, prefix)
                if not count:
                    continue

                # dump
                log.info('collapse "%s" co_filename "%s"', file_path, file_path[len(prefix):])
                fo = open(file_path, 'wb')
                fo.write(magic)
                fo.write(moddate)
                marshal.dump(code, fo)
                fo.close()

    def remove_compiled(self, venv_dir):
        log.info('removing compiled files from "%s"', venv_dir)
        for dir_path, dir_names, file_names in os.walk(venv_dir):
            for file_name in file_names:
                if (not file_name.endswith('pyc') and
                    not file_name.endswith('pyo')):
                    continue
                file_path = os.path.join(dir_path, file_name)
                os.remove(file_path)

    def fixup_code(self, code, filename_prefix):
        count = 0
        consts = []
        for const in code.co_consts:
            if isinstance(const, types.CodeType):
                const, const_count = self.fixup_code(const, filename_prefix)
                count += const_count
            consts.append(const)
        co_filename = code.co_filename
        if co_filename.startswith(filename_prefix):
            co_filename = co_filename[len(filename_prefix):]
            count += 1
        if count:
            code = types.CodeType(
                code.co_argcount,
                code.co_nlocals,
                code.co_stacksize,
                code.co_flags,
                code.co_code,
                tuple(consts),
                code.co_names,
                code.co_varnames,
                co_filename,
                code.co_name,
                code.co_firstlineno,
                code.co_lnotab,
                code.co_freevars,
                code.co_cellvars,
            )
        return code, count

    def fixup_links(self, venv_dir):
        prefix = os.path.abspath(self.bdist_dir)
        for dir_path, dir_names, file_names in os.walk(venv_dir):
            for link_name in dir_names + file_names:
                link_path = os.path.join(dir_path, link_name)
                if not os.path.islink(link_path):
                    continue
                target = os.readlink(link_path)
                if not target.startswith(prefix):
                    continue 
                target = target[len(prefix):]
                log.info('collapse "%s" link "%s"', link_path, target)
                os.unlink(link_path)
                os.symlink(target, link_path)
