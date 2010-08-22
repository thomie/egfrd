NUMPY_INCLUDE_DIR = @NUMPY_INCLUDE_DIR@
PYTHON_INCLUDES = @PYTHON_INCLUDES@

INCLUDES = ${PYTHON_INCLUDES} -I${NUMPY_INCLUDE_DIR}
AM_CXXFLAGS = @CXXFLAGS@ @GSL_CFLAGS@ -I.. -Wall -g -Wstrict-aliasing=0 -Wno-invalid-offsetof -Winvalid-pch
AM_CPPFLAGS = @CPPFLAGS@

noinst_LTLIBRARIES = libbinding_utils.la

libbinding_utils_la_SOURCES = \
	bd_propagator_class.cpp \
	box_class.cpp \
	cylinder_class.cpp \
	domain_classes.cpp \
	domain_id_class.cpp \
	exception_classes.cpp \
	matrix_space_classes.cpp \
	model_class.cpp \
	module_functions.cpp \
	multi_particle_container_class.cpp \
	network_rules_class.cpp \
	network_rules_wrapper_class.cpp \
	particle_class.cpp \
	particle_container_class.cpp \
	particle_id_class.cpp \
	plane_class.cpp \
	position_converters.cpp \
	event_classes.cpp \
	random_number_generator_class.cpp \
	shape_converters.cpp \
	shell_classes.cpp \
	shell_id_class.cpp \
	species_id_class.cpp \
	species_type_class.cpp \
	sphere_class.cpp \
	structure_classes.cpp \
	transaction_classes.cpp \
	world_class.cpp
