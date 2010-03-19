from _gfrd import *
from greens_function_wrapper import *

class Single(object):
    """There are 2 main types of Singles:
        * NonInteractionSingle
        * InteractionSingle (when the particle is nearby a surface)

    Each type of Single defines a list of coordinates, see coordinate.py. For each 
    coordinate the Green's function is specified.

    """
    def __init__(self, domain_id, pid_particle_pair, shell_id, reactiontypes, 
                 surface):
        self.multiplicity = 1

        self.pid_particle_pair = pid_particle_pair
        self.reactiontypes = reactiontypes

        self.k_tot = 0

        self.last_time = 0.0
        self.dt = 0.0
        self.event_type = None

        self.surface = surface

        # Create shell.
        shell = self.create_new_shell(pid_particle_pair[1].position, pid_particle_pair[1].radius, domain_id)

        self.shell_list = [(shell_id, shell), ]

        self.event_id = None

        self.domain_id = domain_id

        self.updatek_tot()

    def getD(self):
        return self.pid_particle_pair[1].D
    D = property(getD)

    def get_shell_id(self):
        return self.shell_list[0][0]
    shell_id = property(get_shell_id)

    def get_shell(self):
        return self.shell_list[0][1]
    shell = property(get_shell)

    def get_shell_id_shell_pair(self):
        return self.shell_list[0]
    def set_shell_id_shell_pair(self, value):
        self.shell_list[0] = value
    shell_id_shell_pair = property(get_shell_id_shell_pair, 
                                   set_shell_id_shell_pair)

    def get_mobility_radius(self):
        return self.shell_list[0][1].shape.radius - self.pid_particle_pair[1].radius

    def get_shell_size(self):
        return self.shell_list[0][1].shape.radius

    def initialize(self, t):
        '''
        Reset the Single.

        Radius (shell size) is shrunken to the actual radius of the particle.
        self.dt is reset to 0.0.  Do not forget to reschedule this Single
        after calling this method.
        '''
        self.dt = 0.0
        self.last_time = t
        self.event_type = EventType.SINGLE_ESCAPE

    def is_reset(self):
        return self.dt == 0.0 and self.event_type == EventType.SINGLE_ESCAPE

    def draw_reaction_time_tuple(self):
        """Return a (reaction time, event type)-tuple.

        """
        if self.k_tot == 0:
            dt = numpy.inf
        elif self.k_tot == numpy.inf:
            dt = 0.0
        else:
            dt = (1.0 / self.k_tot) * math.log(1.0 / myrandom.uniform())
        return dt, EventType.SINGLE_REACTION

    def draw_interaction_time(self):
        """Todo.
        
        Note: we are not calling single.drawEventType() just yet, but 
        postpone it to the very last minute (when this event is executed in 
        fire_single). So IV_EVENT can still be an iv escape or an iv 
        interaction.

        """
        pass

    def draw_escape_or_interaction_time_tuple(self):
        """Return an (escape or interaction time, event type)-tuple.

        Handles also all interaction events.
        
        """
        if self.getD() == 0:
            dt = numpy.inf
        else:
            dt = drawTime_wrapper(self.greens_function())

        event_type = EventType.SINGLE_ESCAPE
        return dt, event_type

    def determine_next_event(self):
        """Return an (event time, event type)-tuple.

        """
        return min(self.draw_escape_or_interaction_time_tuple(),
                   self.draw_reaction_time_tuple())

    def updatek_tot(self):
        self.k_tot = 0

        if not self.reactiontypes:
            return

        for rt in self.reactiontypes:
            self.k_tot += rt.k

    def draw_reaction_rule(self):
        k_array = [rt.k for rt in self.reactiontypes]
        k_array = numpy.add.accumulate(k_array)
        k_max = k_array[-1]

        rnd = myrandom.uniform()
        i = numpy.searchsorted(k_array, rnd * k_max)

        return self.reactiontypes[i]

    def check(self):
        pass

    def __str__(self):
        return 'Single[%s: %s: event_id=%s]' % (self.domain_id, self.pid_particle_pair[0], self.event_id)


class NonInteractionSingle(Single):
    """1 Particle inside a shell, no other particles around. 

    There are 3 types of NonInteractionSingles:
        * SphericalSingle: spherical shell, 3D movement.
        * PlanarSurfaceSingle: cylindrical shell, 2D movement.
        * CylindricalSurfaceSingle: cylindrical shell, 1D movement.

    """
    def __init__(self, domain_id, pid_particle_pair, shell_id, reactiontypes, 
                 surface):
        Single.__init__(self, domain_id, pid_particle_pair, shell_id,
                        reactiontypes, surface)

    def draw_new_position(self, dt, event_type):
        gf = self.greens_function()
        a = self.get_mobility_radius()
        r = draw_displacement_wrapper(gf, dt, event_type, a)
        displacement = self.displacement(r)
        if __debug__:
            scale = self.pid_particle_pair[1].radius
            if feq(length(displacement), abs(r), typical=scale) == False:
                raise AssertionError('displacement != abs(r): %g != %g.' % 
                                     (length(displacement), abs(r)))
        return self.pid_particle_pair[1].position + displacement


class InteractionSingle(Single):
    """Interactions singles are used when a particle is close to a surface.

    There are 2 types of InteractionSingles:
        * PlanarSurfaceInteraction.
        * CylindricalSurfaceInteraction.

    """
    def __init__(self, domain_id, pid_particle_pair, shell_id,  reactiontypes, 
                 surface, interactionType, origin, orientation, size, 
                 particleOffset, projectedPoint, sizeOfDomain):
        # Todo. Make this list smaller.
        self.interactionType = interactionType
        self.origin = origin
        self.orientation = orientation
        self.size = size
        self.particleOffset = particleOffset
        self.projectedPoint = projectedPoint
        self.sizeOfDomain = sizeOfDomain
        Single.__init__(self, domain_id, pid_particle_pair, shell_id,
                        reactiontypes, surface)

    def get_sigma(self):
        try:
            # Todo.
            surface_thickness = self.surface.shape.radius
        except:
            surface_thickness = self.surface.shape.Lz

        return self.pid_particle_pair[1].radius + \
            surface_thickness
    sigma = property(get_sigma)


class SphericalSingle(NonInteractionSingle):
    """1 Particle inside a (spherical) shell not on any surface.

        * Particle coordinate inside shell: r, theta, phi.
        * Coordinate: radial r.
        * Initial position: r = 0.
        * Selected randomly when drawing displacement vector: theta, phi.

    """
    def __init__(self, domain_id, pid_particle_pair, shell_id, reactiontypes, 
                 surface):
        NonInteractionSingle.__init__(self, domain_id, pid_particle_pair, 
                                      shell_id, reactiontypes, surface)

    def greens_function(self):
        return FirstPassageGreensFunction(self.getD(),self.get_mobility_radius())

    def create_new_shell(self, position, radius, domain_id):
        return SphericalShell(domain_id, Sphere(position, radius))

    def displacement(self, r):
        return random_vector(r)

    def __str__(self):
        return 'Spherical' + Single.__str__(self)


class PlanarSurfaceSingle(NonInteractionSingle):
    """1 Particle inside a (cylindrical) shell on a PlanarSurface. (Hockey 
    pucks).

        * Particle coordinates on surface: x, y.
        * Domain: radial r. (determines x and y together with theta).
        * Initial position: r = 0.
        * Selected randomly when drawing displacement vector: theta.

    """
    def __init__(self, domain_id, pid_particle_pair, shell_id, reactiontypes, 
                 surface):
        NonInteractionSingle.__init__(self, domain_id, pid_particle_pair, 
                                      shell_id, reactiontypes, surface)

    def greens_function(self):
        # Todo. 2D gf Abs Sym.
        #gf = FirstPassageGreensFunction2D(self.getD())
        return FirstPassageGreensFunction(self.getD(), self.get_mobility_radius())

    def create_new_shell(self, position, radius, domain_id):
        # The size (thickness) of a hockey puck is not more than it has to be 
        # (namely the radius of the particle), so if the particle undergoes an 
        # unbinding reaction we still have to clear the target volume and the 
        # move may be rejected (NoSpace error).
        orientation = self.surface.shape.unit_z
        size = self.pid_particle_pair[1].radius
        return CylindricalShell(domain_id, Cylinder(position, radius, orientation, size))

    def displacement(self, r):
        x, y = random_vector2D(r)
        return x * self.surface.shape.unit_x + y * self.surface.shape.unit_y

    def __str__(self):
        return 'PlanarSurface' + Single.__str__(self)


class PlanarSurfaceInteraction(InteractionSingle):
    """1 Particle close to a PlanarSurface, inside a cylindrical shell placed 
    on top of the surface.

        * Particle coordinates inside shell: r, theta, z.
        * Coordinates: radial r, cartesian z.
        * Initial position: r = 0, z = z.
        * Selected randomly when drawing displacement vector: theta.

    """
    def __init__(self, domain_id, pid_particle_pair, shell_id, reactiontypes, 
                 surface, interactionType, origin, orientation, size, 
                 particleOffset, projectedPoint=None, sizeOfDomain=None):
        InteractionSingle.__init__(self, domain_id, pid_particle_pair, 
                                   shell_id, reactiontypes, surface, 
                                   interactionType, origin, orientation, size, 
                                   particleOffset, projectedPoint, 
                                   sizeOfDomain)
        # a
        # sigma
        # r0

    def greens_function_r(self):
        # Todo. 2D gf Abs Sym.
        #gf = FirstPassageGreensFunction2D(self.getD())

        gf = FirstPassageGreensFunction(self.getD())
        a = self.get_mobility_radius()
        gf.seta(a)
        return gf

    def greens_function_z(self):
        # Todo. 1D gf Rad Abs should be sigma to a.
        #gf = FirstPassageGreensFunction1DRad(self.D_tot, self.rt.k)

        gf = FirstPassagePairGreensFunction(self.getD(), self.interactionType.k, self.sigma)
        gf.seta(a)
        return gf

        # TODO.

        # Cartesian domain of size L. Correction with getMinRadius().
        #zDomain = CartesianDomain(particleOffset[1] - self.getMinRadius(), 
        #                           sizeOfDomain - 2 * self.getMinRadius(), 
        #                           gfz)

    def createNewShell(self, position, radius, domain_id):
        orientation = self.orientation
        size = self.size
        return CylindricalShell(position, radius, orientation, size, domain_id)

    def draw_new_positions(self, dt, eventType):
        gf_r = self.greens_function_r()
        a = self.get_mobility_radius()
        r = draw_displacement_wrapper(gf_r, dt, eventType, a)
        x, y = randomVector2D(r)

        # Todo. Cartesian coordinate will return absolute position.
        gf_z = self.greens_function_z()
        # Heads up. sizeOfDomain is different from the size of the cylinder, 
        # because the domain ends where the surface starts, while the cylinder 
        # is continuing into the surface.
        a = 1 #TODO 
        r0 = self.particleOffset
        sigma = self.sigma
        z = draw_displacement_wrapper(gf_z, dt, eventType, a, r0, sigma)

        # Add displacement vector to self.particle.pos, not self.pos.
        return self.particle.pos + x * self.interactionSurface.unitX + \
               y * self.interactionSurface.unitY + z * self.shellList[0].unitZ

    def __str__(self):
        return 'PlanarSurfaceInteraction' + Single.__str__(self)


class CylindricalSurfaceSingle(NonInteractionSingle):
    """1 Particle inside a (cylindrical) shell on a CylindricalSurface. 
    (Rods).

        * Particle coordinates on surface: z.
        * Domain: cartesian z.
        * Initial position: z = 0.
        * Selected randomly when drawing displacement vector: none.

    """
    def __init__(self, domain_id, pid_particle_pair, shell_id, reactiontypes, 
                 surface):
        NonInteractionSingle.__init__(self, domain_id, pid_particle_pair, 
                                      shell_id, reactiontypes, surface)

    def greens_function(self):
        # Todo. 1D gf Abs Abs.
        #gf = FirstPassageGreensFunction1D(self.getD(), )
        return FirstPassageGreensFunction(self.getD(), self.get_mobility_radius())

    def create_new_shell(self, position, size, domain_id):
        # Heads up. The cylinder's *size*, not radius, is changed when you 
        # make the cylinder bigger, because of the redefinition of set_radius.

        # The radius of a rod is not more than it has to be (namely the radius 
        # of the particle), so if the particle undergoes an unbinding reaction 
        # we still have to clear the target volume and the move may be 
        # rejected (NoSpace error).
        radius = self.pid_particle_pair[1].radius
        orientation = self.surface.shape.unit_z
        return CylindricalShell(domain_id, Cylinder(position, radius, orientation, size))

    def displacement(self, z):
        # z can be pos or min.
        return z * self.shell_list[0][1].shape.unit_z

    def get_mobility_radius(self):
        # Heads up.
        return self.shell_list[0][1].shape.size - self.pid_particle_pair[1].radius

    def get_shell_size(self):
        # Heads up.
        return self.shell_list[0][1].shape.size

    def __str__(self):
        return 'CylindricalSurface' + Single.__str__(self)


class CylindricalSurfaceInteraction(InteractionSingle):
    """1 Particle close to a CylindricalSurface, inside a cylindrical shell 
    that surrounds the surface.

        * Particle coordinates inside shell: r, theta, z.
        * Domains: composite r-theta, cartesian z.
        * Initial position: r = r, theta = 0, z = z.
        * Selected randomly when drawing displacement vector: none.

    """
    def __init__(self, particle, surface, reactiontypes, interactionType, 
                  origin, radius, orientationVector, size, particleOffset, 
                  projectedPoint, sizeOfDomain=None):
        # Only needed for this type of Interaction.
        self.unitR = normalize(particle.pos - projectedPoint)
        InteractionSingle.__init__(self, particle, surface, reactiontypes, 
                                    interactionType)

        self.shellList = [Cylinder(origin, radius, orientationVector, size)]

        # Interaction possible in r direction.
        self.pgf = FirstPassagePairGreensFunction2D(self.getD(),
                                                     interactionType.k, 
                                                     surface.radius)
        rthetaDomain = CompositeDomain(surface.radius + self.getMinRadius(), 
                                        particleOffset[0], 
                                        radius - self.getMinRadius(), self.pgf)

        # Free diffusion in z direction.
        gfz = FirstPassageGreensFunction1D(self.getD())
        # Cartesian domain of size L. Correction with getMinRadius().
        zDomain = CartesianDomain(particleOffset[1] - self.getMinRadius(), 
                                   sizeOfDomain - 2 * self.getMinRadius(), gfz)

        self.domains = [rthetaDomain, zDomain]

    def draw_new_positions(self, dt):
        r, theta = self.domains[0].drawDisplacement(self.pgf, dt)
        # Cartesian domain returns displacement, not absolute position.
        z = self.domains[1].drawDisplacement(dt)
        # Calculate new position starting from origin.
        newVectorR = r * rotateVector(self.unitR, self.shellList[0].unitZ, 
                                       theta)
        # Orientation matters (plus or minus), so shellList[0].unitZ is used 
        # here instead of surface.unitZ.
        # Add displacement vector to self.particle.pos, not self.pos.
        return self.particle.pos + newVectorR + z * self.shellList[0].unitZ

    def get_mobility_radius(self):
        # Heads up.
        return self.shell_list[0][1].size - self.pid_particle_pair[1].radius

    def get_shell_size(self):
        # Heads up.
        return self.shell_list[0][1].size

    def __str__(self):
        return 'CylindricalSurfaceInteraction' + Single.__str__(self)


class DummySingle(object):
    def __init__(self):
        self.multiplicity = 1
        self.size = 0.0
        self.shellList = [Sphere(NOWHERE, 0.0)]

    def getMinSize(self):
        return 0.0

    def getD(self):
        return 0.0

    def getPos(self):
        return NOWHERE
    pos = property(getPos)

    def __str__(self):
        return 'DummySingle()'

