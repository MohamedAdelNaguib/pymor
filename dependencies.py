#!/usr/bin/env python3
# This file is part of the pyMOR project (https://www.pymor.org).
# Copyright pyMOR developers and contributors. All rights reserved.
# License: BSD 2-Clause License (https://opensource.org/licenses/BSD-2-Clause)

# DO NOT use any python features here that require 3.6 or newer

_PYTEST = 'pytest==7.2.0'
# 5.12.* blocked due to https://bugreports.qt.io/browse/PYSIDE-1004
# however the problem is not actually fixed in 5.12.3 as advertised,
# but only starting from 5.13.1
_PYSIDE = 'PySide2>=5.15.2.1'


def _numpy_scipy():
    # numpy versions with filters according to minimal version with a wheel
    # 1.24 limit due to https://github.com/pymor/pymor/issues/1692
    numpys = [
        'numpy>=1.17.5;python_version == "3.8"',
        'numpy>=1.19.4;python_version == "3.9"',
        'numpy>=1.21.5;python_version >= "3.10"',
    ]
    scipys = [
        'scipy>=1.5.1;python_version == "3.8"',
        'scipy>=1.5.4;python_version == "3.9"',
        'scipy>=1.7.3;python_version >= "3.10"',
    ]
    return numpys + scipys


def setup_requires():
    return [
        'setuptools',
        'wheel',
        'pytest-runner>=2.9',
        'packaging',
    ]


# recheck if jupyter_client pin still necessary
#   https://github.com/jupyter-widgets/pythreejs/issues/366
# Qt bindings selectors are a woraround for https://bugreports.qt.io/browse/QTBUG-88688
# ipywidget pin is due to https://github.com/pymor/pymor/issues/1717
# for jupytext and jupyter_server, see https://github.com/pymor/pymor/issues/1878
install_requires = ['qtpy>2.0', 'packaging', 'diskcache', 'typer', 'click'] + _numpy_scipy()
install_suggests = {
    'ipython>=6.0': 'an enhanced interactive python shell',
    'ipyparallel>=6.2.5': 'required for pymor.parallel.ipython',
    'matplotlib': 'needed for error plots in demo scipts',
    'pyopengl': 'fast solution visualization for builtin discretizations (PySide also required)',
    'sympy': 'symbolic mathematics',
    'pygments': 'highlighting code',
    'pythreejs': 'threejs bindings for python notebook  visualization',
    'jupyter_client>=7.0.6': 'necessary to explicitly state here to fix 3js',
    'jupytext>=1.14.4': 'open Markdown files in Jupyter',
    'jupyter_server>1.3,<2.0': 'required for jupytext',
    _PYTEST: 'testing framework required to execute unit tests',
    _PYSIDE: 'solution visualization for builtin discretizations',
    'ipywidgets<8,>7': 'notebook GUI elements',
    'nbresuse': 'resource usage indicator for notebooks',
    'torch>=1.11.0': 'PyTorch open source machine learning framework',
    'jupyter_contrib_nbextensions': 'modular collection of jupyter extensions',
    'pillow': 'image library used for bitmap data functions',
    'dune-gdt>=2022.5.3; platform_system=="Linux" and platform_machine=="x86_64"': 'generic discretization toolbox',
    'dune-xt>=2022.5.3; platform_system=="Linux" and platform_machine=="x86_64"': 'DUNE extensions for dune-gdt',
}
io_requires = ['pyevtk', 'xmljson', 'meshio>=4.4', 'lxml', 'gmsh']
install_suggests.update({p: 'optional File I/O support libraries' for p in io_requires})
# see https://github.com/pymor/pymor/issues/1915 for contrib-apple
doc_requires = ['sphinx>=5.0,<5.2', 'matplotlib', _PYSIDE, 'ipyparallel>=6.2.5', 'python-slugify',
                'sphinxcontrib-applehelp<1.0.3',
                'ipywidgets<8,>7', 'sphinx-qt-documentation', 'bash_kernel', 'sphinx-material',
                'sphinxcontrib-bibtex', 'sphinx-autoapi>=1.8,<2', 'myst-nb>=0.16'] + install_requires
# Note the hypothesis duplication makes the conda env creation script work
# and is harmless for pip installs
ci_requires = ['check-manifest==0.49',
               'check_reqs==1.0.0',
               # only update in lockstep with sphinx
               'docutils==0.18',
               'flake8-docstrings==1.6.0',
               'flake8-rst-docstrings==0.3.0',
               'hypothesis[numpy,pytest]==6.56.3',
               'hypothesis==6.56.3',
               'pybind11==2.9.2',
               'pypi-oldest-requirements==2022.1.0',
               'pyqt5-qt5==5.15.2',
               'pyqt5==5.15.7',
               _PYTEST,
               'pytest-cov==4.0.0',
               'python-dotenv==0.21.0',
               'python-gitlab==3.12.0',
               'pytest-memprof==0.2.0',
               'pytest-notebook==0.8.1',
               'pytest-parallel==0.1.1',
               'pytest-regressions==2.4.1',
               'pytest-xdist==3.1.0',
               'readme_renderer[md]==37.0',
               'rstcheck==6.1.1',
               'scikit-fem==6.0.0',
               'twine==4.0.2']

# Slycot is pinned due to buildsystem changes + missing wheels
optional_requirements_file_only = (['slycot>=0.4.0', 'pymess',
                                    'mpi4py>=3.0.3;python_version == "3.9"',
                                    'mpi4py>3.0.3;python_version >= "3.10"',
                                    'mpi4py>=3.0;python_version < "3.9"'])


def strip_markers(name):
    for m in ';<>=':
        try:
            i = name.index(m)
            name = name[:i].strip()
        except ValueError:
            continue
    return name


def extras():
    import pkg_resources
    import itertools

    def _candidates(blocklist):
        # skip those which aren't needed in our current environment (py ver, platform)
        for pkg in set(itertools.chain(doc_requires, install_suggests.keys())):
            if pkg in blocklist:
                continue
            try:
                marker = next(pkg_resources.parse_requirements(pkg)).marker
                if marker is None or marker.evaluate():
                    yield pkg
            except pkg_resources.RequirementParseError:
                # try to fake a package to get the marker parsed
                stripped = strip_markers(pkg)
                fake_pkg = 'pip ' + pkg.replace(stripped, '')
                try:
                    marker = next(pkg_resources.parse_requirements(fake_pkg)).marker
                    if marker is None or marker.evaluate():
                        yield pkg
                except pkg_resources.RequirementParseError:
                    continue

    # blocklisted packages need a (minimal) compiler setup
    # - nbresuse, pytest-memprof depend on psutil which has no wheels
    # - slycot directly needs a compiler setup with BLAS, plus scikit-build + cmake
    # - pymess is better installed from source (see README.md)
    return {
        'full': list(_candidates(blocklist=['slycot', 'pymess', 'nbresuse', 'pytest-memprof'])),
        'ci':  ci_requires,
        'docs': doc_requires,
        'io': io_requires,
    }


toml_tpl = '''
[build-system]
requires = {0}
build-backend = "setuptools.build_meta"
'''
if __name__ == '__main__':
    note = '# This file is autogenerated. Edit dependencies.py instead'
    import os
    import itertools
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt'), 'wt') as req:
        req.write(note+'\n')
        for module in sorted(set(itertools.chain(install_requires, setup_requires()))):
            req.write(module+'\n')
    with open(os.path.join(os.path.dirname(__file__), 'requirements-optional.txt'), 'wt') as req:
        req.write(note+'\n')
        req.write('-r requirements.txt\n')
        req.write('-r requirements-ci.txt\n')
        for module in sorted(set(itertools.chain(optional_requirements_file_only,
                                                 doc_requires, install_suggests.keys()))):
            req.write(module+'\n')
    with open(os.path.join(os.path.dirname(__file__), 'requirements-ci.txt'), 'wt') as req:
        req.write('-r requirements.txt\n')
        req.write(note+'\n')
        for module in sorted(ci_requires):
            req.write(module+'\n')
    with open(os.path.join(os.path.dirname(__file__), 'pyproject.toml'), 'wt') as toml:
        toml.write(note)
        toml.write(toml_tpl.format(str(setup_requires())))
