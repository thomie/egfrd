
# BUILT
noinst_LTLIBRARIES = libbinding_utils.la


# FLAGS and LIBS
AM_CPPFLAGS = @PYTHON_INCLUDES@ -I@NUMPY_INCLUDE_DIR@ @BOOST_CPPFLAGS@ -DNO_IMPORT 

AM_CXXFLAGS = @GSL_CFLAGS@ -Winvalid-pch 


# PRECOMPILED HEADERS
PCH_FLAGS = -m128bit-long-double -maccumulate-outgoing-args -fPIC

SUFFIXES: hpp gch
.hpp.gch:
	$(CXXCOMPILE) -c $(PCH_FLAGS) -DNO_IMPORT $<

BUILT_SOURCES = \
	binding_common_WorldTraits.gch\
	binding_common_World.gch\
	binding_common_EGFRDSimulatorTraits.gch\
	binding_common_EGFRDSimulator.gch


# SOURCES
libbinding_utils_la_SOURCES = \
	bd_propagator_class.cpp \
	box_class.cpp \
	ConsoleAppender.cpp \
	cylinder_class.cpp \
	domain_classes.cpp \
	domain_id_class.cpp \
	egfrd_simulator_classes.cpp \
	event_classes.cpp \
	exception_classes.cpp \
	LogAppender.cpp \
	Logger.cpp \
	LoggerManager.cpp \
	matrix_space_classes.cpp \
	model_class.cpp \
	module_functions.cpp \
	multi_particle_container_class.cpp \
	network_rules_class.cpp \
	network_rules_wrapper_class.cpp \
	particle_class.cpp \
	particle_container_class.cpp \
	particle_id_class.cpp \
	particle_model_class.cpp \
	particle_simulator_classes.cpp \
	plane_class.cpp \
	position_converters.cpp \
	PythonAppender.cpp \
	python_logger_classes.cpp \
	random_number_generator_class.cpp \
	reaction_record_classes.cpp \
	shape_converters.cpp \
	shell_classes.cpp \
	shell_id_class.cpp \
	species_id_class.cpp \
	species_type_class.cpp \
	sphere_class.cpp \
	structure_classes.cpp \
	structure_type_class.cpp \
	transaction_classes.cpp \
	world_class.cpp


# DIST
noinst_HEADERS = *.hpp


# CLEAN
CLEANFILES = *.gch
