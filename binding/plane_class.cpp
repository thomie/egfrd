#include "binding_common_EGFRDSimulator.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Plane.hpp"
#include "../Plane.hpp"

namespace binding {
typedef EGFRDSimulator::plane_type Plane;

void register_plane_class()
{
    register_plane_class<Plane>("Plane");
}

} // namespace binding
