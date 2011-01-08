#include "binding_common_EGFRDSimulator.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "../Box.hpp"
#include "Box.hpp"

namespace binding {
typedef EGFRDSimulator::box_type Box;

void register_box_class()
{
    register_box_class<Box>("Box");
}

} // namespace binding
