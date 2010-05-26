import model
import _gfrd
from gfrdbase import throw_in_particles

__all__ = [
    'throw_in',
    'Species',
    'ParticleModel',
    ]

def throw_in(world, st, n, surface=None):
    if surface == None or isinstance(surface, _gfrd.CuboidalRegion):
        # Look up species_type.
        # For alternative user interface.
        st = world.model.get_species_type(st)
    else:
        # Look up species_type, given a species and a surface.
        # For alternative user interface.
        st = world.model.get_species_type((st, surface))

    throw_in_particles(world, st.id, n)


class Species(object):
    def __init__(self, name, D, radius, surface="world"):
        self.name = name
        self.D = D
        self.radius = radius
        self.surface = surface


class ParticleModel(model.ParticleModel):
    '''
    Methods for alternative user interface.

    '''

    def add_species(self, species, surface=None, D=None, radius=None):
        """Add a new species.

        A species is a type of particles. By default the species is added to 
        the 'world'. If a surface is specified, it is added to that surface. Per 
        surface a different diffusion constant D and radius can be specified. 
        By default the ones for the 'world' are used.

        species -- a species created with Species().
        surface -- the surface this species can exist on.
        D       -- the diffusion constant of the particles.
        radius  -- the radii of the particles.

        """
        if surface == None:
            name = species.name
            surface_id = self.get_structure("world").id
        else:
            # Todo.
            #assert any(surface == s for s in self.surface_list.itervalues()), \
            #       '%s not in surface_list.' % (surface)

            # Construct new name if species lives on a surface.
            surface_id = surface.id
            name = '(' + species.name + ',' + str(surface_id) + ')'

        if D == None:
            assert species.D != None, \
                   'Diffusion constant of species %s not specified.' % species
            D = species.D

        if radius == None:
            assert species.radius != None, \
                   'Radius of species %s not specified.' % species
            radius = species.radius

        # Create a species type for internal use. Don't use the user defined 
        # species at all. The new name is a concatenation of the user defined 
        # name and the surface this species exists on.
        new_species_type = model.Species(name, D, radius, surface_id)

        self.add_species_type(new_species_type)

    def get_species_type(self, key):
        """Return species type.

        """
        if isinstance(key, _gfrd.SpeciesType):
            return key
        elif isinstance(key, Species):
            name = key.name
        else:
            # Unpack (species, surface)-key.
            species = key[0]
            surface = key[1]

            if species == 0:
                # This is the virtual product of a decay or surface absorption 
                # reaction.
                species = DummySpecies(surface)

            # Note: see add_species for how name is constructed. 
            name = '(' + species.name + ',' + str(surface.id) + ')'

        return self.get_species_type_by_name(name)

    def get_species_type_by_name(self, name):
        for species_type in self.species_types:
            if species_type['name'] == name:
                return species_type

        raise RuntimeError('Species type %s does not exist.' % (name))

    def add_reaction(self, reactants, products, k): 
        reactants = map(self.get_species_type, reactants)
        products  = map(self.get_species_type, products)

        rr = _gfrd.ReactionRule(reactants, products)
        rr['k'] = '%.16g' % k
        self.network_rules.add_reaction_rule(rr)
        return rr

