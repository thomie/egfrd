#include "binding_common_EGFRDSimulator.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "../Cylinder.hpp"
#include "Cylinder.hpp"

namespace binding {
typedef EGFRDSimulator::cylinder_type Cylinder;

void register_cylinder_class()
{
    register_cylinder_class<Cylinder>("Cylinder");
}

} // namespace binding
