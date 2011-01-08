#include "binding_common_EGFRDSimulator.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Domain.hpp"
#include "ShapedDomain.hpp"
#include "../ShapedDomain.hpp"
#include "Single.hpp"
#include "Pair.hpp"
#include "SphericalSingle.hpp"
#include "CylindricalSingle.hpp"
#include "SphericalPair.hpp"
#include "CylindricalPair.hpp"
#include "Multi.hpp"

namespace binding {
typedef ::ShapedDomain<EGFRDSimulatorTraits> ShapedDomain;
typedef EGFRDSimulator::domain_type Domain;
typedef EGFRDSimulator::spherical_single_type::base_type Single;
typedef EGFRDSimulator::spherical_pair_type::base_type Pair;
typedef EGFRDSimulator::spherical_single_type SphericalSingle;
typedef EGFRDSimulator::cylindrical_single_type CylindricalSingle;
typedef EGFRDSimulator::spherical_pair_type SphericalPair;
typedef EGFRDSimulator::cylindrical_pair_type CylindricalPair;
typedef EGFRDSimulator::multi_type Multi;

void register_domain_classes()
{
    register_domain_class<Domain>("_Domain");
    register_shaped_domain_class<ShapedDomain>("_ShapedDomain");
    register_single_class<Single>("_Single");
    register_pair_class<Pair>("_Pair");
    register_spherical_single_class<SphericalSingle>("_SphericalSingle");
    register_cylindrical_single_class<CylindricalSingle>("_CylindricalSingle");
    register_spherical_pair_class<SphericalPair>("_SphericalPair");
    register_cylindrical_pair_class<CylindricalPair>("_CylindricalPair");
    register_multi_class<Multi>("_Multi");
}

} // namespace binding
