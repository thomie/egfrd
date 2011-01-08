#include "binding_common_EGFRDSimulatorTraits.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "../Multi.hpp"
#include "MultiParticleContainer.hpp"

namespace binding {
typedef ::MultiParticleContainer<EGFRDSimulatorTraits> MultiParticleContainer;

void register_multi_particle_container_class()
{
    register_multi_particle_container_class<MultiParticleContainer, World>("MultiParticleContainer");
}

} // namespace binding
