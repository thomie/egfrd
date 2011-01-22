SUBDIRS = doc binding test


# BESSEL TABLES
# Built the Bessel tables before they are needed
# Manually recording dependencies instead of using BUILT_SOURCES is faster
BUILT_SOURCES = \
	SphericalBesselTable.hpp\
	CylindricalBesselTable.hpp
#SphericalBesselGenerator.lo : SphericalBesselTable.hpp

SphericalBesselTable.hpp: make_sjy_table.py
	@PYTHON@ $(top_srcdir)/make_sjy_table.py SphericalBesselTable.hpp

#CylindricalBesselGenerator.lo : CylindricalBesselTable.hpp

CylindricalBesselTable.hpp: make_cjy_table.py
	@PYTHON@ $(top_srcdir)/make_cjy_table.py CylindricalBesselTable.hpp


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
	abstract_set.hpp\
	AnalyticalPair.hpp\
	AnalyticalSingle.hpp\
	BasicNetworkRulesImpl.hpp\
	BasicReactionRecorderImpl.hpp\
	BDPropagator.hpp\
	BDSimulator.hpp\
	bessel.hpp\
	Box.hpp\
	ConsoleAppender.hpp\
	CuboidalRegion.hpp\
	Cylinder.hpp\
	CylindricalBesselGenerator.hpp\
	CylindricalSurface.hpp\
	Defs.hpp\
	DomainFactory.hpp\
	Domain.hpp\
	DomainID.hpp\
	DomainUtils.hpp\
	DynamicPriorityQueue.hpp\
	EGFRDSimulatorFactory.hpp\
	EGFRDSimulator.hpp\
	EGFRDSimulatorTraits.hpp\
	EventScheduler.hpp\
	exceptions.hpp\
	factorial.hpp\
	filters.hpp\
	findRoot.hpp\
	freeFunctions.hpp\
	funcSum.hpp\
	generator.hpp\
	geometry.hpp\
	GreensFunction1DAbsAbs.hpp\
	GreensFunction1DRadAbs.hpp\
	GreensFunction3DAbs.hpp\
	GreensFunction3DAbsSym.hpp\
	GreensFunction3D.hpp\
	GreensFunction3DRadAbsBase.hpp\
	GreensFunction3DRadAbs.hpp\
	GreensFunction3DRadInf.hpp\
	GreensFunction3DSym.hpp\
	GreensFunction.hpp\
	GSLRandomNumberGenerator.hpp\
	gsl_rng_base.hpp\
	HalfOrderBesselGenerator.hpp\
	Identifier.hpp\
	linear_algebra.hpp\
	Logger.hpp\
	MatrixSpace.hpp\
	Model.hpp\
	Multi.hpp\
	NetworkRules.hpp\
	NetworkRulesWrapper.hpp\
	OldDefs.hpp\
	PairGreensFunction.hpp\
	Pair.hpp\
	ParticleContainerBase.hpp\
	ParticleContainer.hpp\
	Particle.hpp\
	ParticleID.hpp\
	ParticleModel.hpp\
	ParticleSimulationStructure.hpp\
	ParticleSimulatorFactory.hpp\
	ParticleSimulator.hpp\
	PlanarSurface.hpp\
	Plane.hpp\
	Point.hpp\
	PyEventScheduler.hpp\
	ReactionRecorder.hpp\
	ReactionRecord.hpp\
	ReactionRule.hpp\
	ReactionRuleInfo.hpp\
	Region.hpp\
	SerialIDGenerator.hpp\
	ShapedDomain.hpp\
	Shape.hpp\
	Shell.hpp\
	ShellID.hpp\
	Single.hpp\
	sorted_list.hpp\
	SpeciesInfo.hpp\
	SpeciesType.hpp\
	SpeciesTypeID.hpp\
	Sphere.hpp\
	SphericalBesselGenerator.hpp\
	SphericalSurface.hpp\
	Structure.hpp\
	StructureType.hpp\
	StructureUtils.hpp\
	Surface.hpp\
	Transaction.hpp\
	twofold_container.hpp\
	utils.hpp\
	Vector3.hpp\
	World.hpp\
	WorldTraits.hpp\
	compat.h\
	peer/py_hash_support.hpp\
	peer/util/to_python_converter_fun.hpp\
	peer/util/shared_const_ptr.hpp\
	peer/util/exception_translators.hpp\
	peer/util/reference_accessor_wrapper.hpp\
	peer/util/instance_holder.hpp\
	peer/util/to_native_converter.hpp\
	peer/util/range_from_range.hpp\
	peer/converters/iterator.hpp\
	peer/converters/tuple/to_python.hpp\
	peer/converters/tuple/from_python.hpp\
	peer/converters/generator/to_python.hpp\
	peer/converters/generator/from_python.hpp\
	peer/converters/iterator/to_python.hpp\
	peer/converters/tuple.hpp\
	peer/converters/sequence.hpp\
	peer/converters/sequence/to_python.hpp\
	peer/converters/sequence/from_python.hpp\
	peer/utils.hpp\
	peer/numpy/ndarray_converters.hpp\
	peer/numpy/scalar_converters.hpp\
	peer/numpy/type_mappings.hpp\
	peer/numpy/pyarray_backed_allocator.hpp\
	peer/numpy/wrapped_multi_array.hpp\
	peer/set_indexing_suite.hpp\
	peer/wrappers/generator/pyiterator_generator.hpp\
	peer/wrappers/generator/generator_wrapper.hpp\
	peer/wrappers/iterator/stl_iterator_wrapper.hpp\
	peer/wrappers/iterator/pyseq_iterator.hpp\
	peer/wrappers/range/pyiterable_range.hpp\
	peer/wrappers/range/stl_container_wrapper.hpp\
	peer/wrappers/exception/exception_wrapper.hpp\
	peer/pickle_support.hpp\
	peer/compat.h\
	utils/array_helper.hpp\
	utils/array_traits.hpp\
	utils/assoc_container_traits.hpp\
	utils/base_type_walker.hpp\
	utils/fun_composition.hpp\
	utils/fun_wrappers.hpp\
	utils/get_default_impl.hpp\
	utils/get_mapper_mf.hpp\
	utils/map_adapter.hpp\
	utils/math.hpp\
	utils/memberwise_compare.hpp\
	utils/pair.hpp\
	utils/pointer_as_ref.hpp\
	utils/pointer_preds.hpp\
	utils/random.hpp\
	utils/range.hpp\
	utils/range_support.hpp\
	utils/reference_or_instance.hpp\
	utils/reset.hpp\
	utils/stringizer.hpp\
	utils/swap.hpp\
	utils/unassignable_adapter.hpp

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

