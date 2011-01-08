#include "binding_common_World.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "ParticleContainer.hpp"

namespace binding {
typedef World::base_type::base_type ParticleContainer; 

void register_particle_container_class()
{
    register_particle_container_class<ParticleContainer>("ParticleContainer");
}

} // namespace binding
