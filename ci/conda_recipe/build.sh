#!/bin/bash

if [[ "$(uname)" == Linux ]]; then
    pushd $PREFIX/lib
    ln -s libtcl8.5.so libtcl.so
    ln -s libtk8.5.so libtk.so
    popd
fi

python setup.py setopt -cpackages -otests -sfalse
python setup.py setopt -cpackages -otoolkits_tests -sfalse
python setup.py setopt -cpackages -osample_data -sfalse
python setup.py setopt -crc_options -obackend -sqt4agg

# the macosx backend isn't building with conda at this stage.
if [[ "$(uname)" == Darwin ]]; then
python setup.py setopt -cgui_support -otkaagg -strue
python setup.py setopt -cgui_support -omacosx -sfalse
fi

cat setup.cfg

$PYTHON setup.py install --single-version-externally-managed --record=record.txt
