#include "binding_common_EGFRDSimulatorTraits.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include <boost/python.hpp>
#include "ReactionRecord.hpp"
#include "reaction_recorder_converter.hpp"

namespace binding {
typedef EGFRDSimulatorTraits::reaction_record_type ReactionRecord;
typedef EGFRDSimulatorTraits::reaction_recorder_type ReactionRecorder;

void register_reaction_record_classes()
{
    register_reaction_record_class<ReactionRecord>("ReactionRecord");
    register_reaction_recorder_converter<ReactionRecorder>();
}

} // namespace binding
