#include "binding_common_EGFRDSimulator.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Structure.hpp"
#include "ParticleSimulationStructure.hpp"
#include "Surface.hpp"
#include "Region.hpp"
#include "PlanarSurface.hpp"
#include "CylindricalSurface.hpp"
#include "SphericalSurface.hpp"
#include "CuboidalRegion.hpp"

namespace binding {
typedef WorldTraits::structure_type Structure;
typedef EGFRDSimulator::particle_simulation_structure_type ParticleSimulationStructure;
typedef EGFRDSimulator::surface_type Surface;
typedef EGFRDSimulator::region_type Region;
typedef EGFRDSimulator::planar_surface_type PlanarSurface;
typedef EGFRDSimulator::spherical_surface_type SphericalSurface;
typedef EGFRDSimulator::cylindrical_surface_type CylindricalSurface;
typedef EGFRDSimulator::cuboidal_region_type CuboidalRegion;

void register_structure_classes()
{
    register_structure_class<Structure>("Structure");
    register_particle_simulation_structure_class<ParticleSimulationStructure>("ParticleSimulationStructure");
    register_surface_class<Surface>("Surface");
    register_region_class<Region>("Region");
    register_cuboidal_region_class<CuboidalRegion>("CuboidalRegion");
    register_planar_surface_class<PlanarSurface>("PlanarSurface");
    register_spherical_surface_class<SphericalSurface>("SphericalSurface");
    register_cylindrical_surface_class<CylindricalSurface>("CylindricalSurface");
}

} // namespace binding

