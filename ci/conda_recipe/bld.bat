set LIBPATH=%LIBRARY_LIB%;
set INCLUDE=%INCLUDE%;%PREFIX%\Library\include\freetype2

%PYTHON% setup.py setopt -cpackages -otests -sfalse
%PYTHON% setup.py setopt -cpackages -otoolkits_tests -sfalse
%PYTHON% setup.py setopt -cpackages -osample_data -sfalse

%PYTHON% setup.py install --single-version-externally-managed --record=record.txt
if errorlevel 1 exit 1
