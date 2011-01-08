#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include <boost/python.hpp>
#include "peer/wrappers/generator/generator_wrapper.hpp"
#include "peer/converters/generator/to_python.hpp"
#include "ReactionRule.hpp"
#include "NetworkRules.hpp"

// TODO: Why is this include necessary?
#include "../EGFRDSimulator.hpp"

namespace binding {
typedef ::NetworkRules NetworkRules;
typedef NetworkRules::reaction_rule_generator ReactionRuleGenerator;

static void register_reaction_rule_generator_class()
{
    peer::wrappers::generator_wrapper<
        ptr_generator<
            ReactionRuleGenerator,
            std::auto_ptr<ReactionRuleGenerator> > >::__register_class("ReactionRuleGenerator");
    boost::python::to_python_converter<
            ReactionRuleGenerator*,
            peer::converters::ptr_generator_to_pyiterator_converter<
                ReactionRuleGenerator,
                std::auto_ptr<ReactionRuleGenerator> > >();
}

static void register_reaction_rule_class()
{
    register_reaction_rule_class<ReactionRule>("ReactionRule");
}

void register_network_rules_class()
{
    register_network_rules_class<NetworkRules>("NetworkRules");
    register_reaction_rule_class();
    register_reaction_rule_generator_class();
}

} // namespace binding
