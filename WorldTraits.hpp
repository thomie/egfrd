#ifndef WORLD_TRAITS_HPP
#define WORLD_TRAITS_HPP

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "geometry.hpp"
#include "GSLRandomNumberGenerator.hpp"
#include "Particle.hpp"
#include "ParticleID.hpp"
#include "SerialIDGenerator.hpp"
#include "SpeciesInfo.hpp"
#include "SpeciesTypeID.hpp"
#include "Structure.hpp"
//#include "Surface.hpp"
//#include "Region.hpp"

template<typename Tderived_, typename Tlen_, typename TD_>
struct WorldTraitsBase
{
    typedef std::size_t size_type;
    typedef Tlen_ length_type;
    typedef TD_ D_type;
    typedef TD_ v_type;
    typedef ParticleID particle_id_type;
    typedef SerialIDGenerator<particle_id_type> particle_id_generator;
    typedef SpeciesTypeID species_id_type;
    typedef Particle<length_type, D_type, species_id_type> particle_type;
    typedef std::string structure_id_type;
    typedef SpeciesInfo<species_id_type, D_type, length_type, structure_id_type> species_type;
    typedef Vector3<length_type> point_type;
    typedef typename particle_type::shape_type::position_type position_type;
    typedef GSLRandomNumberGenerator rng_type;
    typedef Structure<Tderived_> structure_type;

    static const Real TOLERANCE = 1e-7;
};

template<typename Tlen_, typename TD_>
struct CyclicWorldTraits: public WorldTraitsBase<CyclicWorldTraits<Tlen_, TD_>, Tlen_, TD_>
{
public:
    typedef WorldTraitsBase<CyclicWorldTraits<Tlen_, TD_>, Tlen_, TD_> base_type;
    typedef typename base_type::length_type length_type;
    typedef typename base_type::position_type position_type;

    template<typename Tval_>
    static Tval_ apply_boundary(Tval_ const& v, length_type const& world_size)
    {
        return ::apply_boundary(v, world_size);
    }

    static length_type cyclic_transpose(length_type const& p0, length_type const& p1, length_type const& world_size)
    {
        return ::cyclic_transpose(p0, p1, world_size);
    }

    static position_type cyclic_transpose(position_type const& p0, position_type const& p1, length_type const& world_size)
    {
        return ::cyclic_transpose(p0, p1, world_size);
    }

    template<typename T1_, typename T2_>
    static length_type distance(T1_ const& p0, T2_ const& p1, length_type const& world_size)
    {
        return distance_cyclic(p0, p1, world_size);
    }

    template<typename Toc_, typename Tfun_, typename Tsphere_>
    static void each_neighbor(Toc_& oc, Tfun_& fun, Tsphere_ const& pos)
    {
        oc.each_neighbor_cyclic(oc.index(pos), fun);
    }

    template<typename Toc_, typename Tfun_, typename Tsphere_>
    static void each_neighbor(Toc_ const& oc, Tfun_& fun, Tsphere_ const& pos)
    {
        oc.each_neighbor_cyclic(oc.index(pos), fun);
    }

    template<typename Toc_, typename Tfun_, typename Tsphere_>
    static void take_neighbor(Toc_& oc, Tfun_& fun, const Tsphere_& cmp)
    {
        take_neighbor_cyclic(oc, fun, cmp);
    }

    template<typename Toc_, typename Tfun_, typename Tsphere_>
    static void take_neighbor(Toc_ const& oc, Tfun_& fun, const Tsphere_& cmp)
    {
        take_neighbor_cyclic(oc, fun, cmp);
    }
};

#endif /* WORLD_TRAITS_HPP */
