ACLOCAL_AMFLAGS=-I m4

SUBDIRS = binding doc test 

TOPSRCDIR = ${top_srcdir}

LTDL_SHLIB_EXT = @LTDL_SHLIB_EXT@

PYTHON = @PYTHON@
PYTHON_PREFIX = @PYTHON_PREFIX@
PYTHON_VERSION = @PYTHON_VERSION@

NUMPY_INCLUDE_DIR=@NUMPY_INCLUDE_DIR@
PYTHON_INCLUDES = @PYTHON_INCLUDES@

pkgpyexecdir = @pkgpyexecdir@

LIBPYTHON = -lpython$(PYTHON_VERSION)

INCLUDES = ${PYTHON_INCLUDES} -I${NUMPY_INCLUDE_DIR}
AM_CXXFLAGS = @CXXFLAGS@ @GSL_CFLAGS@ -Winvalid-pch
LIBBOOSTPYTHON = -l@BOOST_PYTHON_LIBNAME@
LIBBOOSTDATE = -l@BOOST_DATE_TIME_LIBNAME@

CFLAGS = @GSL_CFLAGS@ @BOOST_CPPFLAGS@

PYCHECKER = @PYCHECKER@
PYCHECKER_FLAGS = --limit 0 

noinst_PYTHON = \
	bd.py\
	gfrdbase.py\
	logger.py\
	gfrdbase.py\
	utils.py\
	egfrd.py\
	gfrd.py\
	surface.py\
	single.py\
	dimer.py  


lib_LTLIBRARIES = _gfrd.la _greens_functions.la

_gfrd_la_CPPFLAGS = -DPY_ARRAY_UNIQUE_SYMBOL=PyArray_API

_gfrd_la_SOURCES=\
	freeFunctions.cpp\
	pyGFRD.cpp\
	Model.cpp\
	SpeciesType.cpp\
	BasicNetworkRulesImpl.cpp\
	NetworkRules.cpp\
	Logger.cpp\
	utils.cpp

_greens_functions_la_SOURCES=\
	findRoot.cpp\
	funcSum.cpp\
	greens_functions.cpp\
	SphericalBesselGenerator.cpp\
	freeFunctions.cpp\
	GreensFunction3DSym.cpp\
	GreensFunction3DAbsSym.cpp\
	GreensFunction3DRadInf.cpp\
	GreensFunction3D.cpp\
	GreensFunction3DRadAbs.cpp\
	GreensFunction3DAbs.cpp\
	Logger.cpp

_gfrd_la_LDFLAGS = -module -export-dynamic -avoid-version $(no_undefined)
_gfrd_la_LIBADD = binding/libbinding_utils.la
_gfrd_la_LIBADD += $(LIBBOOSTPYTHON) $(LIBBOOSTDATE) $(LIBPYTHON) $(GSL_LIBS)

_greens_functions_la_LDFLAGS = -module -export-dynamic -avoid-version $(no_undefined)
_greens_functions_la_LIBADD = $(LIBBOOSTPYTHON) $(LIBBOOSTDATE) $(LIBPYTHON) $(GSL_LIBS)

CLEANFILES = \
	SphericalBesselTable.hpp\
	CylindricalBesselTable.hpp

BUILT_SOURCES = \
	SphericalBesselTable.hpp\
	CylindricalBesselTable.hpp

SphericalBesselTable.hpp: make_sjy_table.py
	$(PYTHON) make_sjy_table.py SphericalBesselTable.hpp

CylindricalBesselTable.hpp: make_cjy_table.py
	$(PYTHON) make_cjy_table.py CylindricalBesselTable.hpp


_gfrd.so: _gfrd.la 
	ln -sf .libs/_gfrd.so ./_gfrd.so

_greens_functions.so: _greens_functions.la
	ln -sf .libs/_greens_functions.so ./_greens_functions.so

all-local: _gfrd.so _greens_functions.so

clean-local:
	rm -f _gfrd.so _greens_functions.so


pycheck:
	$(PYCHECKER) $(PYCHECKER_FLAGS) $(top_srcdir)/egfrd.py


dist-hook:
	rm -rf `find $(distdir)/samples -name '.svn'`


EXTRA_DIST = \
	autogen.sh\
	samples\
	make_sjy_table.py
