#ifndef WORLD_HPP
#define WORLD_HPP

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "ParticleContainerBase.hpp"

#include <map>
#include <boost/lexical_cast.hpp>
#include <boost/array.hpp>
#include <boost/utility/enable_if.hpp>
#include <boost/type_traits/is_same.hpp>
#include "exceptions.hpp"
#include "generator.hpp"
#include "filters.hpp"
#include "Transaction.hpp"
#include "Point.hpp" // XXX: workaround. should be removed later.
#include "utils/pair.hpp"
#include "WorldTraits.hpp"

template<typename Tlen_, typename TD_>
struct WorldTraits: public WorldTraitsBase<WorldTraits<Tlen_, TD_>, Tlen_, TD_>
{
public:
    typedef WorldTraitsBase<WorldTraits<Tlen_, TD_>, Tlen_, TD_> base_type;
    typedef typename base_type::length_type length_type;
    typedef typename base_type::position_type position_type;

    template<typename Tval_>
    static Tval_ apply_boundary(Tval_ const& v, length_type const& world_size)
    {
        return v;
    }

    template<typename Tval_>
    static Tval_ cyclic_transpose(Tval_ const& p0, Tval_ const& p1, length_type const& world_size)
    {
        return p0;
    }

    template<typename T1_, typename T2_>
    static length_type distance(T1_ const& p0, T2_ const& p1, length_type const& world_size)
    {
        return ::distance(p0, p1);
    }

    template<typename Toc_, typename Tfun_, typename Tsphere_>
    static void each_neighbor(Toc_& oc, Tfun_& fun, Tsphere_ const& pos)
    {
        oc.each_neighbor(oc.index(pos), fun);
    }

    template<typename Toc_, typename Tfun_, typename Tsphere_>
    static void each_neighbor(Toc_ const& oc, Tfun_& fun, Tsphere_ const& pos)
    {
        oc.each_neighbor(oc.index(pos), fun);
    }

    template<typename Toc_, typename Tfun_, typename Tsphere_>
    static void take_neighbor(Toc_& oc, Tfun_& fun, const Tsphere_& cmp)
    {
        take_neighbor(oc, fun, cmp);
    }

    template<typename Toc_, typename Tfun_, typename Tsphere_>
    static void take_neighbor(Toc_ const& oc, Tfun_& fun, const Tsphere_& cmp)
    {
        take_neighbor(oc, fun, cmp);
    }
};

template<typename Ttraits_>
class World: public ParticleContainerBase<World<Ttraits_>, Ttraits_>
{
public:
    typedef Ttraits_ traits_type;
    typedef ParticleContainerBase<World> base_type;
    typedef ParticleContainer<traits_type> particle_container_type;
    typedef typename traits_type::length_type length_type;
    typedef typename traits_type::species_type species_type;
    typedef typename traits_type::position_type position_type;
    typedef typename traits_type::particle_type particle_type;
    typedef typename traits_type::particle_id_type particle_id_type;
    typedef typename traits_type::particle_id_generator particle_id_generator;
    typedef typename traits_type::species_id_type species_id_type;
    typedef typename traits_type::particle_type::shape_type particle_shape_type;
    typedef typename traits_type::size_type size_type;
    typedef typename traits_type::structure_id_type structure_id_type;
    typedef typename traits_type::structure_type structure_type;
    typedef std::pair<const particle_id_type, particle_type> particle_id_pair;

protected:
    typedef std::map<species_id_type, species_type> species_map;
    typedef std::map<structure_id_type, boost::shared_ptr<structure_type> > structure_map;
    typedef std::set<particle_id_type> particle_id_set;
    typedef std::map<species_id_type, particle_id_set> per_species_particle_id_set;
    typedef select_second<typename species_map::value_type> species_second_selector_type;
    typedef select_second<typename structure_map::value_type> surface_second_selector_type;

public:
    typedef boost::transform_iterator<species_second_selector_type,
            typename species_map::const_iterator> species_iterator;
    typedef boost::transform_iterator<surface_second_selector_type,
            typename structure_map::const_iterator> surface_iterator;
    typedef sized_iterator_range<species_iterator> species_range;
    typedef sized_iterator_range<surface_iterator> structures_range;

public:
    World(length_type world_size = 1., size_type size = 1)
        : base_type(world_size, size) {}

    virtual particle_id_pair new_particle(species_id_type const& sid,
            position_type const& pos)
    {
        species_type const& species(get_species(sid));
        particle_id_pair retval(pidgen_(),
            particle_type(sid, particle_shape_type(pos, species.radius()),
                          species.D(), species.v() ));
        update_particle(retval);
        return retval;
    }

    virtual bool update_particle(particle_id_pair const& pi_pair)
    {
        typename base_type::particle_matrix_type::iterator i(
                base_type::pmat_.find(pi_pair.first));
        if (i != base_type::pmat_.end())
        {
            if ((*i).second.sid() != pi_pair.second.sid())
            {
                particle_pool_[(*i).second.sid()].erase((*i).first);
                particle_pool_[pi_pair.second.sid()].insert(pi_pair.first);
            }
            base_type::pmat_.update(i, pi_pair);
            return false;
        }
        BOOST_ASSERT(base_type::update_particle(pi_pair));
        particle_pool_[pi_pair.second.sid()].insert(pi_pair.first);
        return true;
    }

    virtual bool remove_particle(particle_id_type const& id)
    {
        bool found(false);
        particle_id_pair pp(get_particle(id, found));
        if (!found)
        {
            return false;
        }
        particle_pool_[pp.second.sid()].erase(id);
        base_type::remove_particle(id);
        return true;
    }

    void add_species(species_type const& species)
    {
        species_map_[species.id()] = species;
        particle_pool_[species.id()] = particle_id_set();
    }

    virtual species_type const& get_species(species_id_type const& id) const
    {
        typename species_map::const_iterator i(species_map_.find(id));
        if (species_map_.end() == i)
        {
            throw not_found(std::string("Unknown species (id=") + boost::lexical_cast<std::string>(id) + ")");
        }
        return (*i).second;
    }

    species_range get_species() const
    {
        return species_range(
            species_iterator(species_map_.begin(), species_second_selector_type()),
            species_iterator(species_map_.end(), species_second_selector_type()),
            species_map_.size());
    }

    bool add_structure(boost::shared_ptr<structure_type> surface)
    {
        return structure_map_.insert(std::make_pair(surface->id(), surface)).second;
    }

    virtual boost::shared_ptr<structure_type> get_structure(structure_id_type const& id) const
    {
        typename structure_map::const_iterator i(structure_map_.find(id));
        if (structure_map_.end() == i)
        {
            throw not_found(std::string("Unknown surface (id=") + boost::lexical_cast<std::string>(id) + ")");
        }
        return (*i).second;
    }

    structures_range get_structures() const
    {
        return structures_range(
            surface_iterator(structure_map_.begin(), surface_second_selector_type()),
            surface_iterator(structure_map_.end(), surface_second_selector_type()),
            structure_map_.size());
    }

    particle_id_set get_particle_ids(species_id_type const& sid) const
    {
        typename per_species_particle_id_set::const_iterator i(
            particle_pool_.find(sid));
        if (i == particle_pool_.end())
        {
            throw not_found(std::string("Unknown species (id=") + boost::lexical_cast<std::string>(sid) + ")");
        }
        return (*i).second;
    }

private:
    particle_id_generator pidgen_;
    species_map species_map_;
    structure_map structure_map_;
    per_species_particle_id_set particle_pool_;
};

#endif /* WORLD_HPP */
