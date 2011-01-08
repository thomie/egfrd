#include "binding_common_EGFRDSimulatorTraits.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "BDPropagator.hpp"
#include "../BDPropagator.hpp"

namespace binding {
typedef ::BDPropagator<EGFRDSimulatorTraits> BDPropagator;

void register_bd_propagator_class()
{
    register_bd_propagator_class<BDPropagator>("BDPropagator");
}

} // namespace binding
