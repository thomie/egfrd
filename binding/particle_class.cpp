#include "binding_common_WorldTraits.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Particle.hpp"

namespace binding {
typedef WorldTraits::particle_type Particle;

void register_particle_class()
{
    ParticleWrapper<Particle>::__register_class("Particle");
}

} // namespace binding
