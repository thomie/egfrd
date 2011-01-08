#ifndef EGFRDSIMULATOR_TRAITS_HPP
#define EGFRDSIMULATOR_TRAITS_HPP

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Domain.hpp"
#include "DomainID.hpp"
#include "ParticleSimulator.hpp"
#include "EventScheduler.hpp"
#include "SerialIDGenerator.hpp"
#include "Shell.hpp"
#include "ShellID.hpp"

template<typename Tworld_>
struct EGFRDSimulatorTraitsBase: public ParticleSimulatorTraitsBase<Tworld_>
{
    typedef ParticleSimulatorTraitsBase<Tworld_> base_type;
    typedef Tworld_ world_type;
    typedef ShellID shell_id_type;
    typedef DomainID domain_id_type;
    typedef SerialIDGenerator<shell_id_type> shell_id_generator;
    typedef SerialIDGenerator<domain_id_type> domain_id_generator; typedef Domain<EGFRDSimulatorTraitsBase> domain_type;
    typedef std::pair<const domain_id_type, boost::shared_ptr<domain_type> > domain_id_pair;
    typedef int event_id_type;
    typedef EventScheduler<typename base_type::time_type> event_scheduler_type;
    typedef typename event_scheduler_type::Event event_type;
    typedef typename event_scheduler_type::value_type event_id_pair_type;

    template<typename Tshape_>
    struct shell_generator
    {
        typedef Shell<Tshape_, domain_id_type> type;
    };

    static const Real SAFETY = 1. + 1e-5;
    static const Real SINGLE_SHELL_FACTOR = .1;
    static const Real DEFAULT_DT_FACTOR = 1e-5;
    static const Real CUTOFF_FACTOR = 5.6;
};

#endif /* EGFRDSIMULATOR_TRAITS_HPP */
