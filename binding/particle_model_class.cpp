#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "ParticleModel.hpp"
#include "../ParticleModel.hpp"

namespace binding {
typedef ::ParticleModel ParticleModel;

void register_particle_model_class()
{
    register_particle_model_class<ParticleModel>("ParticleModel");
}

} // namesapce binding
