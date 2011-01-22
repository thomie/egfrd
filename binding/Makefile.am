
# BUILT
noinst_LTLIBRARIES = libbinding_utils.la


# FLAGS and LIBS
AM_CPPFLAGS = @PYTHON_INCLUDES@ -I@NUMPY_INCLUDE_DIR@ @BOOST_CPPFLAGS@ -DNO_IMPORT 

AM_CXXFLAGS = @GSL_CFLAGS@ -I$(top_srcdir) -Winvalid-pch 


# PRECOMPILED HEADERS
PCH_FLAGS = -m128bit-long-double -maccumulate-outgoing-args -fPIC

SUFFIXES: hpp gch
.hpp.gch:
	$(CXXCOMPILE) -c $(PCH_FLAGS) -DNO_IMPORT -o $@ $<

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
noinst_HEADERS = \
	bd_propagator_class.hpp\
	BDPropagator.hpp\
	binding_common_EGFRDSimulator.hpp\
	binding_common_EGFRDSimulatorTraits.hpp\
	binding_common_World.hpp\
	binding_common_WorldTraits.hpp\
	box_class.hpp\
	Box.hpp\
	ConsoleAppender.hpp\
	CuboidalRegion.hpp\
	cylinder_class.hpp\
	Cylinder.hpp\
	CylindricalPair.hpp\
	CylindricalSingle.hpp\
	CylindricalSurface.hpp\
	domain_classes.hpp\
	Domain.hpp\
	domain_id_class.hpp\
	egfrd_simulator_classes.hpp\
	EGFRDSimulator.hpp\
	event_classes.hpp\
	Event.hpp\
	EventScheduler.hpp\
	exception_classes.hpp\
	fcpair_reference_accessor_wrapper.hpp\
	Identifier.hpp\
	LogAppender.hpp\
	Logger.hpp\
	LoggerManager.hpp\
	matrix_space_classes.hpp\
	MatrixSpace.hpp\
	model_class.hpp\
	Model.hpp\
	module_functions.hpp\
	Multi.hpp\
	multi_particle_container_class.hpp\
	MultiParticleContainer.hpp\
	network_rules_class.hpp\
	NetworkRules.hpp\
	network_rules_wrapper_class.hpp\
	NetworkRulesWrapper.hpp\
	Pair.hpp\
	particle_class.hpp\
	particle_container_class.hpp\
	ParticleContainer.hpp\
	Particle.hpp\
	particle_id_class.hpp\
	particle_model_class.hpp\
	ParticleModel.hpp\
	ParticleSimulationStructure.hpp\
	particle_simulator_classes.hpp\
	ParticleSimulator.hpp\
	PlanarSurface.hpp\
	plane_class.hpp\
	Plane.hpp\
	position_converters.hpp\
	PythonAppender.hpp\
	PythonEvent.hpp\
	python_logger_classes.hpp\
	random_number_generator_class.hpp\
	RandomNumberGenerator.hpp\
	reaction_record_classes.hpp\
	reaction_recorder_converter.hpp\
	ReactionRecord.hpp\
	ReactionRule.hpp\
	ReactionRuleInfo.hpp\
	Region.hpp\
	SerialIDGenerator.hpp\
	shape_converters.hpp\
	ShapedDomain.hpp\
	shell_classes.hpp\
	Shell.hpp\
	shell_id_class.hpp\
	Single.hpp\
	species_id_class.hpp\
	SpeciesInfo.hpp\
	species_type_class.hpp\
	SpeciesType.hpp\
	sphere_class.hpp\
	Sphere.hpp\
	SphericalPair.hpp\
	SphericalSingle.hpp\
	SphericalSurface.hpp\
	structure_classes.hpp\
	Structure.hpp\
	structure_type_class.hpp\
	StructureType.hpp\
	Surface.hpp\
	transaction_classes.hpp\
	Transaction.hpp\
	world_class.hpp\
	World.hpp

# CLEAN
CLEANFILES = *.gch
