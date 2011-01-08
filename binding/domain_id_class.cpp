#include "binding_common_EGFRDSimulatorTraits.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Identifier.hpp"
#include "SerialIDGenerator.hpp"

namespace binding {
typedef EGFRDSimulatorTraits::domain_id_type DomainID;

void register_domain_id_class()
{
    IdentifierWrapper<DomainID>::__register_class("DomainID");
    register_serial_id_generator_class<DomainID>("DomainIDGenerator");
}

} // namespace binding
