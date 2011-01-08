#include "binding_common_WorldTraits.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Identifier.hpp"
#include "SerialIDGenerator.hpp"
#include "peer/utils.hpp"

namespace binding {
typedef WorldTraits::species_id_type SpeciesID;

void register_species_id_class()
{
    IdentifierWrapper<SpeciesID>::__register_class("SpeciesID");
    register_serial_id_generator_class<SpeciesID>("SpeciesIDGenerator");
}

} // namespace binding
