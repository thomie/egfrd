#include "binding_common_EGFRDSimulator.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "../Sphere.hpp"
#include "Sphere.hpp"

namespace binding {
typedef EGFRDSimulator::sphere_type Sphere;

void register_sphere_class()
{
    register_sphere_class<Sphere>("Sphere");
}

} // namespace binding

