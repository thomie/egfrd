#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "../Model.hpp"
#include "Model.hpp"

// TODO: Why is this include necessary?
#include "../EGFRDSimulator.hpp"

namespace binding {
typedef ::Model Model;

void register_model_class()
{
    register_model_class<Model>("Model");
}

} // namesapce binding
