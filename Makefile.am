SUBDIRS = doc binding test


# BESSEL TABLES
# Built the Bessel tables before they are needed
# Manually recording dependencies instead of using BUILT_SOURCES is faster
SphericalBesselGenerator.lo : SphericalBesselTable.hpp

SphericalBesselTable.hpp: make_sjy_table.py
	@PYTHON@ make_sjy_table.py SphericalBesselTable.hpp

CylindricalBesselGenerator.lo : CylindricalBesselTable.hpp

CylindricalBesselTable.hpp: make_cjy_table.py
	@PYTHON@ make_cjy_table.py CylindricalBesselTable.hpp


# BUILT
# Make libtool static libraries first
noinst_LTLIBRARIES = \
	lib_gfrd.la\
	lib_greens_functions.la

# Install dlopenable modules in pyexecdir
pkgpyexec_LTLIBRARIES = \
	_gfrd.la\
	_greens_functions.la

all-local: \
	_gfrd.so \
	_greens_functions.so 

_gfrd.so: _gfrd.la 
	ln -sf .libs/_gfrd.so ./_gfrd.so

_greens_functions.so: _greens_functions.la
	ln -sf .libs/_greens_functions.so ./_greens_functions.so


# FLAGS and LIBS
ACLOCAL_AMFLAGS=-I m4

AM_CPPFLAGS = @PYTHON_INCLUDES@ -I@NUMPY_INCLUDE_DIR@ @BOOST_CPPFLAGS@

AM_CXXFLAGS = @GSL_CFLAGS@ 

lib_greens_functions_la_LIBADD = $(GSL_LIBS)

# dlopenable modules are wrappers around static libraries
_gfrd_la_LIBADD = binding/libbinding_utils.la lib_gfrd.la lib_greens_functions.la $(GSL_LIBS) 

_greens_functions_la_LIBADD = lib_greens_functions.la

_gfrd_la_LDFLAGS = -export-dynamic -module -avoid-version $(no_undefined)

_greens_functions_la_LDFLAGS = -export-dynamic -module -avoid-version $(no_undefined)


# SOURCES
# If a .cpp files is needed by both _gfrd and _greens_functions, supply it to 
# the latter, because _greens_functions will be linked in with _gfrd.
lib_gfrd_la_SOURCES=\
	BasicNetworkRulesImpl.cpp\
	Model.cpp\
	NetworkRules.cpp\
	ParticleModel.cpp\
	pyGFRD.cpp\
	SpeciesType.cpp\
	StructureType.cpp\
	utils.cpp

lib_greens_functions_la_SOURCES=\
	ConsoleAppender.cpp\
	findRoot.cpp\
	freeFunctions.cpp\
	funcSum.cpp\
	GreensFunction1DAbsAbs.cpp\
	GreensFunction1DRadAbs.cpp\
	GreensFunction3DSym.cpp\
	GreensFunction3DAbsSym.cpp\
	GreensFunction3DRadInf.cpp\
	GreensFunction3D.cpp\
	GreensFunction3DRadAbsBase.cpp\
	GreensFunction3DRadAbs.cpp\
	GreensFunction3DAbs.cpp\
	greens_functions.cpp\
	Logger.cpp\
	SphericalBesselGenerator.cpp

_gfrd_la_SOURCES=

_greens_functions_la_SOURCES=

nobase_pkgpython_PYTHON = \
	__init__.py\
	bd.py\
	constants.py\
	dumper.py\
	egfrd.py\
	gfrdbase.py\
	gillespie.py\
	greens_function_wrapper.py\
	logger.py\
	model.py\
	multi.py\
	myrandom.py\
	pair.py\
	single.py\
	utils.py\
	visualization/helix.py\
	visualization/__init__.py\
	visualization/pipeline.py\
	visualization/vtklogger.py\
	visualization/vtk_xml_serial_unstructured.py


# CHECK
# Note: there is no macro for @PYCHECKER@ in configure.ac.
PYCHECKER = @PYCHECKER@ --limit 0 
pycheck:
	$(PYCHECKER) $(top_srcdir)/egfrd.py


# INSTALL
# Install samples in docdir
# Note: nobase_doc_DATA can not handle directories recursively
install-data-local: distclean-local
	@$(NORMAL_INSTALL)
	for FILE in `find samples -type f`; do \
	  $(INSTALL_DATA) -D $$FILE $(DESTDIR)$(docdir)/$$FILE; \
	done


# UNINSTALL
# Uninstall samples
uninstall-local:
	@$(NORMAL_UNINSTALL)
	rm -rf $(DESTDIR)$(docdir)/samples


# DIST
dist_pkgpython_DATA = \
	visualization/tensorGlyph.xml \
	visualization/tensorGlyphWithCustomSource.xml

# The only reason to list the headers is for distribution.
nobase_noinst_HEADERS = \
	*.hpp\
	compat.h\
	peer/compat.h\
	peer/converters/generator/*.hpp\
	peer/converters/*.hpp\
	peer/converters/iterator/*.hpp\
	peer/converters/sequence/*.hpp\
	peer/converters/tuple/*.hpp\
	peer/*.hpp\
	peer/numpy/*.hpp\
	peer/util/*.hpp\
	peer/wrappers/exception/*.hpp\
	peer/wrappers/generator/*.hpp\
	peer/wrappers/iterator/*.hpp\
	peer/wrappers/range/*.hpp\
	utils/*.hpp

EXTRA_DIST = \
	autogen.sh\
	CylindricalBesselGenerator.cpp\
	datafile.py\
	gui\
	.hgignore\
	legacy.py\
	make_cjy_table.py\
	make_sjy_table.py\
	misc\
	samples

# Remove these files from temp directory just before .tar.gz is created.
# (nodist__gfrd_la_SOURCES doesn't work because of *.hpp in HEADERS)
dist-hook:
	rm -f $(distdir)/samples/benchmark/Makefile
	rm -rf $(distdir)/samples/benchmark/.deps
	rm -f $(distdir)/SphericalBesselTable.hpp
	rm -f $(distdir)/CylindricalBesselTable.hpp


# CLEAN
CLEANFILES = \
	_gfrd.so\
	_greens_functions.so\
	CylindricalBesselTable.hpp\
	SphericalBesselTable.hpp

cleanless:
	rm -f *.so *.la .libs/*.so .libs/*.la

distclean-local:
	rm -rf samples/benchmark/Makefile samples/benchmark/.deps

