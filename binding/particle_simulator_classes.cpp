#include "binding_common_EGFRDSimulatorTraits.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "../ParticleSimulator.hpp"
#include "ParticleSimulator.hpp"

namespace binding {
typedef ::ParticleSimulator<EGFRDSimulatorTraits> ParticleSimulator;

void register_particle_simulator_classes()
{
    register_particle_simulator_class<ParticleSimulator>("_ParticleSimulator");
}

} // namespace binding
