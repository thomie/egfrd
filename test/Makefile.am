
# BUILT
check_PROGRAMS = $(CPP_TESTS)


# FLAGS and LIBS
AM_CPPFLAGS = @PYTHON_INCLUDES@ -I@NUMPY_INCLUDE_DIR@ @BOOST_CPPFLAGS@

AM_CXXFLAGS = @GSL_CFLAGS@

BDPropagator_test_LDADD = ../BasicNetworkRulesImpl.lo ../NetworkRules.lo ../Logger.lo ../ConsoleAppender.lo ../freeFunctions.lo $(GSL_LIBS)

# Link static libraries, because linking modules is not portable.
# Opionally only list the required .lo files here for a smaller output file.
EGFRDSimulator_test_LDADD = ../lib_gfrd.la ../lib_greens_functions.la $(GSL_LIBS)

EGFRDSimulator_test_CPPFLAGS = -DDEBUG

model_test_LDADD = ../Model.lo ../NetworkRules.lo ../BasicNetworkRulesImpl.lo ../SpeciesType.lo

SphericalBesselGenerator_test_LDADD = ../SphericalBesselGenerator.lo $(GSL_LIBS) 

StructureUtils_test_LDADD = $(GSL_LIBS)


# SOURCES
AM_DEFAULT_SOURCE_EXT = .cpp


# TESTS
TESTS = $(CPP_TESTS) $(PYTHON_TESTS)

CPP_TESTS =\
	array_helper_test\
	BDPropagator_test\
	DynamicPriorityQueue_test\
	EGFRDSimulator_test\
	filters_test\
	geometry_test\
	linear_algebra_test\
	MatrixSpace_test\
	MatrixSpaceWithCylinders_test\
	model_test\
	pointer_as_ref_test\
	py_range_converters_test \
	range_support_test\
	SphericalBesselGenerator_test\
	StructureUtils_test\
	Vector3_test\
	World_test

PYTHON_TESTS = \
	BDSimulator_test.py \
	CylindricalSurface_test.py \
	CylindricalShellContainer_test.py \
	EGFRDSimulator_test.py \
	EventScheduler_test.py \
	freeFunctions_test.py \
	GreensFunction3DRadAbs_test.py \
	GreensFunction3DRadInf_test.py \
	GreensFunction3DAbs_test.py \
	GreensFunction3DAbsSym_test.py \
	GreensFunction3DSym_test.py \
	GreensFunction3D_test.py \
	Model_test.py \
	NetworkRules_test.py \
	NetworkRulesWrapper_test.py \
	PlanarSurface_test.py \
	ReactionRule_test.py \
	ReactionRecord_test.py \
	SphericalShellContainer_test.py \
	utils_test.py

TESTS_ENVIRONMENT = PYTHONPATH=$(top_srcdir)

#%.py:
#	$(TESTS_ENVIRONMENT) @PYTHON@ $<


# DIST
EXTRA_DIST=\
	$(PYTHON_TESTS)\
	$(CPP_OLD)\
	$(PYTHON_OLD)

CPP_OLD=\
	AllTests.cpp\
	BDSimulator_test.cpp\
	CylindricalBesselGenerator_test.cpp\
	position_test.cpp\
	SphericalBesselTable_test.cpp

PYTHON_OLD=\
	alltests.py\
	fpp1test.py\
	GreensFunction1DAbsAbs_test.py\
	GreensFunction1DRadAbs_test.py\
	p.py\
	test.py

