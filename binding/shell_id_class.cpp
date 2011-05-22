#include "binding_common_EGFRDSimulatorTraits.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Identifier.hpp"
#include "SerialIDGenerator.hpp"
#include "peer/utils.hpp"

namespace binding {
typedef EGFRDSimulatorTraits::shell_id_type ShellID;

void register_shell_id_class()
{
    IdentifierWrapper<ShellID>::__register_class("ShellID");
    register_serial_id_generator_class<ShellID>("ShellIDGenerator");
}

} // namespace binding
