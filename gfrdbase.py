 #!/usr/env python


import math
import sys

import numpy
import scipy


from surface import *
import _gfrd
from utils import *

import os
import logging
import logging.handlers

import myrandom

__all__ = [
    'log',
    'setup_logging',
    'p_free',
    'NoSpace',
    'ReactionRuleCache',
    'ParticleModel',
    'World',
    'create_unimolecular_reaction_rule',
    'create_decay_reaction_rule',
    'create_binding_reaction_rule',
    'create_unbinding_reaction_rule',
    'Reaction',
    'ParticleSimulatorBase',
    'Species',
    ]

World = _gfrd.World

log = logging.getLogger('ecell')

def setup_logging():
    global log 

    if 'LOGFILE' in os.environ:
        if 'LOGSIZE' in os.environ and int(os.environ['LOGSIZE']) != 0:
            handler = logging.handlers.\
                RotatingFileHandler(os.environ['LOGFILE'], mode='w',
                                    maxBytes=int(os.environ['LOGSIZE']))
        else:
            handler = logging.FileHandler(os.environ['LOGFILE'], 'w', )
            
    else:
        handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    if __debug__:
        log.addHandler(handler)
        
    LOGLEVELS = { 'CRITICAL': logging.CRITICAL,
                  'ERROR': logging.ERROR,
                  'WARNING': logging.WARNING,
                  'INFO': logging.INFO, 
                  'DEBUG': logging.DEBUG, 
                  'NOTSET': logging.NOTSET }

    if 'LOGLEVEL' in os.environ:
        if __debug__:
            log.setLevel(LOGLEVELS[os.environ['LOGLEVEL']])
    else:
        if __debug__:
            log.setLevel(logging.INFO)


setup_logging()


def p_free(r, t, D):
    Dt4 = D * t * 4.0
    Pi4Dt = numpy.pi * Dt4
    rsq = r * r
    
    p = math.exp(- rsq / Dt4) / math.sqrt(Pi4Dt * Pi4Dt * Pi4Dt)

    jacobian = 4.0 * numpy.pi * rsq

    return p * jacobian
    

class NoSpace(Exception):
    pass


class ReactionRuleCache(object):
    def __init__(self, rt, products, k):
        self.rt = rt
        self.products = products
        self.k = k


class Species(object):
    """For alternative user interface.

    """
    def __init__(self, name, D=None, radius=None, surface=None):
        self.name = name
        self.D = D
        self.radius = radius
        self.surface = surface


class ParticleModel(_gfrd.Model):
    def __init__(self):
        _gfrd.Model.__init__(self)

        self.surface_list = {}
        self.interactionRuleMap = {}

        # Particles of a Species whose surface is not specified will be added 
        # to the world. Dimensions don't matter, except for visualization.
        self.default_surface = \
            CuboidalRegion([0, 0, 0], [1.0, 1.0, 1.0], 'world')

    def set_default_surface_size(self, size):
        # Particles of a Species whose surface is not specified will be added 
        # to the world. Dimensions don't matter, except for visualization.
        self.default_surface = \
            CuboidalRegion([0, 0, 0], [size, size, size], 'world')

    def new_species_type(self, id, D, radius):
        st = _gfrd.Model.new_species_type(self)
        st["id"] = str(id)
        st["D"] = str(D)
        st["radius"] = str(radius)
        return st

    def set_all_repulsive(self):
        nr = self.network_rules
        # Maybe the user has defined a reaction rule for any 2 species since a 
        # previous call to this method, so remove *all* repulsive reaction 
        # rules first.
        for species1 in self.species_types:
            for species2 in self.species_types:
                gen = nr.query_reaction_rule(species1, species2)
                if gen is not None:
                    for reaction_rule in gen:
                        if float(reaction_rule['k']) == 0.0:
                            nr.remove_reaction_rule(reaction_rule)

        # Reactions.
        for species1 in self.species_types:
            for species2 in self.species_types:
                gen = nr.query_reaction_rule(species1, species2)
                if gen is None or len(set(gen)) == 0:
                    rr = _gfrd.ReactionRule([species1, species2], [])
                    rr['k'] = '0.0'
                    nr.add_reaction_rule(rr)

        # Interactions.
        for species in self.species_types:
            for surface in self.surfaceList.iterkeys():
                try:
                    self.interactionRuleMap[(species, surface)]
                except:
                    ir = _gfrd.ReactionRule([species], [])
                    ir['k'] = '0.0'
                    self.interactionRuleMap[(species, surface)] = ir

    def add_planar_surface(self, name, origin, vector_x, vector_y, Lx, Ly, Lz=0):
        """Add a planar surface.

        name -- a descriptive name, should not be omitted.

        origin -- [x0, y0, z0] is the *center* of the planar surface.
        vector_x -- [x1, y1, z1] and
        vector_y -- [x2, y2, z2] are 2 perpendicular vectors that don't have 
        to be normalized that span the plane. For example [1,0,0] and [0,1,0]
        for a plane at z=0.

        Lx -- lx and 
        Ly -- ly are the distances from the origin of the plane along vector_x 
            or vector_y *to an edge* of the plane. PlanarSurfaces are finite.
        Lz -- dz, the thickness of the planar surface, can be omitted for Lz=0.

        """
        return self.add_surface(PlanarSurface(name, origin, vector_x, vector_y,
                                             Lx, Ly, Lz))

    def add_cylindrical_surface(self, name, origin, radius, orientation, size):
        """Add a cylindrical surface.

        name -- a descriptive name, should not be omitted.

        origin -- [x0, y0, z0] is the *center* of the cylindrical surface.
        radius -- r is the radis of the cylinder.
        orientation -- [x1, y1, z1] is a vector that doesn't have to
            normalized that defines the orienation of the cylinder. For 
            example [0,0,1] for a for a cylinder along the z-axis.
        size -- lz is the distances from the origin of the cylinder along 
            the oriention vector to the end of the cylinder. So effectively
            the *half-length*. CylindricalSurfaces are finite.

        """
        return self.add_surface(CylindricalSurface(name, origin, radius, 
                                                  orientation, size))

    def add_surface(self, surface):
        if(not isinstance(surface, Surface) or
           isinstance(surface, CuboidalRegion)):
            raise RuntimeError(str(surface) + ' is not a surface.')

        self.surface_list[surface.name] = surface
        return surface

    def get_surface(self, name_of_surface): 
        if name_of_surface != self.default_surface.name:
            surface = self.surface_list[name_of_surface]
        else:
            # Default surface is not stored in surface_list, because it's not 
            # really a surface, and should not be found in get_closest_surface 
            # searches.
            surface = self.default_surface
        return surface

    def dump_reaction_rule(self, reaction_rule):
        '''Pretty print reaction rule.

        ReactionRule.__str__ would be good, but we are actually getting a 
        ReactionRuleInfo or ReactionRuleCache object.

        '''
        buf = ('k=%.3g' % reaction_rule.k + ': ').ljust(15)
        for index, sid in enumerate(reaction_rule.rt.reactants):
            if index != 0:
                buf += ' + '
            reactant = self.get_species_type_by_id(sid)
            buf += reactant['id'].ljust(15)
        if len(reaction_rule.products) == 0:
            if reaction_rule.k != 0:
                buf += '..decays'
        else:
            buf += '-> '

        for index, sid in enumerate(reaction_rule.products):
            if index != 0:
                buf += ' + '
            product = self.get_species_type_by_id(sid)
            buf += product['id'].ljust(15)

        return buf + '\n'

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
            surface = self.default_surface
        else:
            assert any(surface == s for s in self.surface_list.itervalues()), \
                   '%s not in surface_list.' % (surface)

            # Construct new name if species lives on a surface.
            name = '(' + species.name + ',' + str(surface) + ')'

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
        species_type = self.new_species_type(name, D, radius)
        species_type['surface'] = surface.name

        return species_type

    def get_species_type(self, key):
        """Return species type.

        """
        if isinstance(key, SpeciesType):
            return key
        elif isinstance(key, Species):
            name = key.name
        else:
            # Unpack (species, surface)-key.
            species = key[0]
            surface = key[1]

            if species == 0:
                # This is the virtual product of a decay or surface absorption 
                # reaction. DummySpeciesType.
                return {'surface': surface}

            # Note: see add_species for how name is constructed. 
            name = '(' + species.name + ',' + str(surface) + ')'

        return self.get_species_type_by_name(name)

    def get_species_type_by_name(self, name):
        for species_type in self.species_types:
            if species_type['id'] == name:
                return species_type

        raise RuntimeError('Species type %s does not exist.' % (name))

    def add_reaction(self, reactants, products, k): 
        reactants = map(self.get_species_type, reactants)
        products  = map(self.get_species_type, products)

        # Check for interactions.
        if len(products) == 1:
            reactantSurface = reactants[0]['surface']
            productSurface = products[0]['surface']

            if(reactantSurface == self.defaultSurface.name and
               productSurface != self.defaultSurface.name):
                # Remove DummySpeciesType from products list. Were needed for 
                # surface absorption reaction.
                products = [product for product in products if
                            isinstance(product, _gfrd.SpeciesType)]

                ir = _gfrd.ReactionRule(reactants, products)
                ir['k'] = '%.16g' % k
                # Surface binding is not a Poisson process, so this reaction 
                # rule should not be added to the reaction list but to the 
                # interaction list.
                self.interactionRuleMap[(reactants[0], productSurface)] = ir
                return

        rr = _gfrd.ReactionRule(reactants, products)
        rr['k'] = '%.16g' % k
        self.network_rules.add_reaction_rule(rr)
        return rr

    def isSurfaceBindingReactionRule(self, rr):
        # Since a surface a surface absorption reaction doesn't have a product 
        # species we can not check for the productSurface as we do for 
        # isSurfaceUnbindingReactionRule etc.
        # This check always works, but don't call it before the interaction is 
        # added to the interactionRuleMap.
        return any([rr == ir for ir in self.interactionRuleMap.values()])

    def isSurfaceUnbindingReactionRule(self, rr):
        reactantSurface = rr.reactants[0].surface
        productSurface = rr.products[0].surface

        return (reactantSurface != self.defaultSurface and
                productSurface == self.defaultSurface)

    def isDirectSurfaceBindingReactionRule(self, rr):
        reactantSurface1 = rr.reactants[0].surface
        reactantSurface2 = rr.reactants[1].surface
        productSurface = rr.products[0].surface

        return xor((reactantSurface1 == self.defaultSurface and
                    reactantSurface2 != self.defaultSurface and
                    reactantSurafce2 == productSurface),
                  ((reactantSurface2 == self.defaultSurface and
                    reactantSurface1 != self.defaultSurface and
                    reactantSurface1 == productSurface)))

    def isDirectSurfaceUnbindingReactionRule(self, rr):
        reactantSurface = rr.reactants[0].surface
        productSurface1 = rr.products[0].surface
        productSurface2 = rr.products[1].surface

        return(reactantSurface != self.defaultSurface and
               xor(productSurface1 == self.defaultSurface,
                   productSurface2 == self.defaultSurface))


def create_unimolecular_reaction_rule(s1, p1, k):
    rr = _gfrd.ReactionRule([s1, ], [p1, ])
    rr['k'] = '%.16g' % k
    return rr


def create_decay_reaction_rule(s1, k):
    rr = _gfrd.ReactionRule([s1, ], [])
    rr['k'] = '%.16g' % k
    return rr


def create_binding_reaction_rule(s1, s2, p1, k):
    rr = _gfrd.ReactionRule([s1, s2], [p1, ])
    rr['k'] = '%.16g' % k
    return rr


def create_unbinding_reaction_rule(s1, p1, p2, k):
    rr = _gfrd.ReactionRule([s1, ], [p1, p2])
    rr['k'] = '%.16g' % k
    return rr


class Reaction:
    def __init__(self, type, reactants, products):
        self.type = type
        self.reactants = reactants
        self.products = products

    def __str__(self):
        return 'Reaction(' + str(self.type) + ', ' + str(self.reactants)\
           + ', ' + str(self.products) + ')'


class ParticleSimulatorBase(object):
    def __init__(self, world):
        self.particle_pool = {}
        self.reaction_rule_cache = {}

        #self.dt = 1e-7
        #self.t = 0.0

        self.H = 3.0

        self.dissociation_retry_moves = 1
        
        self.dt_limit = 1e-3
        self.dt_max = self.dt_limit

        # counters
        self.rejected_moves = 0
        self.reaction_events = 0

        self.world = world

        self.max_matrix_size = 0

        self._distance_sq = None
        self._disatnce_sq_array = None

        self.last_reaction = None

        self.model = ParticleModel()

        self.network_rules = None

    def set_model(self, model):
        model.set_all_repulsive()
        model.set_default_surface_size(self.world.world_size)
        self.reaction_rule_cache.clear()

        for st in model.species_types:
            if st["surface"] == "":
                st["surface"] = self.model.default_surface.name

            try:
                self.world.get_species(st.id)
            except:
                self.world.add_species(_gfrd.SpeciesInfo(st.id, 
                                                   float(st["D"]), 
                                                   float(st["radius"]), 
                                                   st["surface"]))
            # else: keep species info for this species.

            if not self.particle_pool.has_key(st.id):
                self.particle_pool[st.id] = _gfrd.ParticleIDSet()
            # else: keep particle data for this species.

        self.network_rules = _gfrd.NetworkRulesWrapper(model.network_rules)
        self.model = model

    def initialize(self):
        pass

    def get_closest_surface(self, pos, ignore):
        """Return sorted list of tuples with:
            - distance to surface
            - surface itself

        We can not use matrix_space, it would miss a surface if the origin of the 
        surface would not be in the same or neighboring cells as pos.

        """
        surfaces = [None]
        distances = [numpy.inf]

        ignore_surfaces = []
        for obj in ignore:
            if isinstance(obj.surface, Surface):
                # For example ignore surface that particle is currently on.
                ignore_surfaces.append(obj.surface)

        for surface in self.model.surface_list.itervalues():
            if surface not in ignore_surfaces:
                pos_transposed = \
                    self.world.cyclic_transpose(pos, surface.shape.position)
                distance_to_surface = self.distance(surface.shape, pos_transposed)
                distances.append(distance_to_surface)
                surfaces.append(surface)

        return min(zip(distances, surfaces))

    def get_closest_surface_within_radius(self, pos, radius, ignore):
        """Return sorted list of tuples with:
            - distance to surface
            - surface itself

        """
        distance_to_surface, closest_surface = self.get_closest_surface(pos, 
                                                                   ignore) 
        if distance_to_surface < radius:
            return distance_to_surface, closest_surface
        else:
            return numpy.inf, None

        if isinstance(size, float) and size == INF:
            self._distance = distance
        else:
            self._distance = distance_cyclic

    def apply_boundary(self, pos):
        return self.world.apply_boundary(pos)

    def get_reaction_rule1(self, species):
        k = (species, )
        try:
            retval = self.reaction_rule_cache[k]
        except:
            gen = self.network_rules.query_reaction_rule(species)
            if gen is None:
                retval = None
            else:
                retval = []
                for rt in gen:
                    products = [self.world.get_species(sid) for sid in rt.products]
                    species1 = self.world.get_species(rt.reactants[0])
                    if len(products) == 1:
                        if species1.radius * 2 < products[0].radius:
                            raise RuntimeError,\
                                'radius of product must be smaller ' \
                                + 'than radius of reactant.'
                    elif len(products) == 2:
                        if species1.radius < products[0].radius or\
                                species1.radius < products[1].radius:
                            raise RuntimeError,\
                                'radii of both products must be smaller than ' \
                                + 'reactant.radius.'
                    retval.append(ReactionRuleCache(rt, products, rt.k))
            self.reaction_rule_cache[k] = retval
        return retval

    def get_reaction_rule2(self, species1, species2):
        if species2 < species1:
            k = (species2, species1)
        else:
            k = (species1, species2)
        try:
            retval = self.reaction_rule_cache[k]
        except:
            gen = self.network_rules.query_reaction_rule(species1, species2)
            if gen is None:
                retval = None
            else:
                retval = []
                for rt in gen:
                    retval.append(
                        ReactionRuleCache(
                            rt,
                            [self.world.get_species(sid) for sid in rt.products],
                            rt.k))
            self.reaction_rule_cache[k] = retval
        if __debug__:
            if len(retval) > 1:
                name1 = self.model.get_species_type_by_id(species1)['id']
                name2 = self.model.get_species_type_by_id(species2)['id']
                raise RuntimeError('More than 1 bimolecular reaction rule '
                                   'defined for %s + %s: %s' %
                                   (name1, name2, retval))
        return retval

    def getInteractionRule(self, species, surface):
        # Todo. This is a mess.
        ir = self.model.interactionRuleMap.get((species, surface))
        return ReactionRuleCache(
                   ir,  
                   [self.world.get_species(sid) for sid in products],
                   k)
    
    def get_species(self):
        return self.world.species

    def get_particle_pool(self, sid):
        return self.particle_pool[sid]

    def get_first_pid(self, sid):
        return iter(self.particle_pool[sid]).next()

    def get_position(self, object):
        if type(object) is tuple and type(object[0]) is _gfrd.ParticleID:
            pid = object[0]
        elif type(object) is _gfrd.ParticleID:
            pid = object
        elif type(object) is _gfrd.Particle:
            pid = self.get_first_pid(object.sid)
        elif type(object) is _gfrd.SpeciesTypeID:
            pid = self.get_first_pid(object)

        return self.world.get_particle(pid)[1].position

    def distance_between_particles(self, object1, object2):
        pos1 = self.get_position(object1) 
        pos2 = self.get_position(object2)
        return self.distance(pos1, pos2)

    def distance(self, position1, position2):
        return self.world.distance(position1, position2)
        
    def set_all_repulsive(self):
        # TODO
        pass
        
    def throw_in_particles(self, st, n, surface=None):
        if surface == None or isinstance(surface, CuboidalRegion):
            # Look up species_type.
            # For alternative user interface.
            st = self.model.get_species_type(st)
        else:
            # Look up species_type, given a species and a surface.
            # For alternative user interface.
            st = self.model.get_species_type((st, surface))
        species = self.world.get_species(st.id)
        if surface == None:
            surface = self.model.get_surface(species.surface_id)

        if __debug__:
            log.info('\tthrowing in %s %s particles to %s' % (n, species.id,
                                                              surface))

        # This is a bit messy, but it works.
        i = 0
        while i < int(n):
            position = surface.random_position()

            # Check overlap.
            if not self.get_particles_within_radius(position, species.radius):
                create = True
                # Check if not too close to a neighbouring surfaces for 
                # particles added to the world, or added to a self-defined 
                # box.
                if surface == self.model.default_surface or \
                   (surface != self.model.default_surface and 
                    isinstance(surface, CuboidalRegion)):
                    distance, closest_surface = \
                        self.get_closest_surface(position, [])
                    if (closest_surface and
                        distance < closest_surface.minimal_distance_from_surface(
                                   species.radius)):
                        if __debug__:
                            log.info('\t%d-th particle rejected. Too close to '
                                     'surface. I will keep trying.' % i)
                        create = False
                if create:
                    # All checks passed. Create particle.
                    p = self.create_particle(st.id, position)
                    i += 1
                    if __debug__:
                        log.info(p)
            elif __debug__:
                log.info('\t%d-th particle rejected. I will keep trying.' % i)

    def place_particle(self, st, pos):
        species = self.world.get_species(st.id)
        pos = numpy.array(pos)
        radius = species.radius

        if self.get_particles_within_radius(pos, radius):
            raise NoSpace, 'overlap check failed'
            
        particle = self.create_particle(st.id, pos)
        return particle

    def create_particle(self, sid, pos):
        pid_particle_pair = self.world.new_particle(sid, pos)
        self.particle_pool[sid].add(pid_particle_pair[0])
        return pid_particle_pair

    def remove_particle(self, pid_particle_pair):
        self.particle_pool[pid_particle_pair[1].sid].remove(pid_particle_pair[0])
        self.world.remove_particle(pid_particle_pair[0])

    def move_particle(self, pid_particle_pair):
        self.world.update_particle(pid_particle_pair)

    def get_particles_within_radius(self, pos, radius, ignore=[]):
        return self.world.check_overlap((pos, radius), ignore)

    def clear(self):
        self.dt_max = self.dt_limit
        self.dt = self.dt_limit

    def check_particle_matrix(self):
        total = sum(len(pool) for pool in self.particle_pool.itervalues())

        if total != self.world.num_particles:
            raise RuntimeError,\
                'total number of particles %d != self.world.num_particles %d'\
                % (total, self.world.num_particles)

    def check_particles(self):
        for pid_particle_pair in self.world:
            pid = pid_particle_pair[0]
            pos = pid_particle_pair[1].position
            if (pos >= self.world.world_size).any() or (pos < 0.0).any():
                raise RuntimeError,\
                    '%s at position %s out of the world (world size=%g).' %\
                    (pid, pos, self.world.world_size)


    def check(self):
        self.check_particle_matrix()
        self.check_particles()

    def dump_population(self):
        buf = ''
        for sid, pool in self.particle_pool.iteritems():
            buf += str(sid) + ':' + str(pool) + '\t'

        return buf

    def dump_reaction_rules(self):
        reaction_rules_1 = []
        reaction_rules_2 = []
        interactions = []
        reflective_reaction_rules = []
        for si1 in self.world.species:
            for reaction_rule_cache in self.get_reaction_rule1(si1.id):
                string = self.model.dump_reaction_rule(reaction_rule_cache)
                reaction_rules_1.append(string)
            for si2 in self.world.species:
                for reaction_rule_cache in self.get_reaction_rule2(si1.id, si2.id):
                    string = self.model.dump_reaction_rule(reaction_rule_cache)
                    if reaction_rule_cache.k > 0:
                        reaction_rules_2.append(string)
                    else:
                        reflective_reaction_rules.append(string)

        # Interactions.
        interaction_rules_string = ''
        for (species, surface), interaction in \
            self.model.interactionRuleMap.iteritems():
            # Ignore reflecting.
            if float(interaction['k']) > 0:
                interaction_rules_string += self.model.dump_reaction_rule(interaction) + " (" + str(surface) + ")" + '\n'

        reaction_rules_1 = uniq(reaction_rules_1)
        reaction_rules_1.sort()
        reaction_rules_2 = uniq(reaction_rules_2)
        reaction_rules_2.sort()
        reflective_reaction_rules = uniq(reflective_reaction_rules)
        reflective_reaction_rules.sort()

        return('\nMonomolecular reaction rules:\n' + ''.join(reaction_rules_1) +
               '\nBimolecular reaction rules:\n' + ''.join(reaction_rules_2) +
               '\nInteractions between a particle and a surface:\n' + 
               interaction_rules_string +
               '\nReflective bimolecular reaction rules:\n' +
               ''.join(reflective_reaction_rules))


