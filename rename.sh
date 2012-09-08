#!/bin/sh

FILES='
Makefile.am
*.hpp
*.cpp
*.py
test/Makefile.am
test/*.cpp
test/*.py
binding/Makefile.am
binding/*.hpp
binding/*.cpp'

REGEXP='
s/FirstPassageGreensFunction1DRad/GreensFunction1DRadAbs/g;
s/FirstPassageGreensFunction1D/GreensFunction1DAbsAbs/g;
s/BasicPairGreensFunction/GreensFunction3DRadInf/g;
s/FirstPassageGreensFunction/GreensFunction3DAbsSym/g;
s/FirstPassageNoCollisionPairGreensFunction/GreensFunction3DAbs/g;
s/FirstPassagePairGreensFunction/GreensFunction3DRadAbs/g;
s/FreeGreensFunction/GreensFunction3DSym/g;
s/FreePairGreensFunction/GreensFunction3D/g'

sed -i "$REGEXP" $FILES
rename "$REGEXP" $FILES
