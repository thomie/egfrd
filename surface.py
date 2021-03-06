import math
import numpy
import myrandom

from single import *
from pair import *
from utils import *

PlanarSurfaceInteraction=None
CylindricalSurfaceInteraction=None

class Surface(object):
    """Surface should be added to the egfrd simulator by calling 
    sim.add_surface().

    """
    def __init__(self, name):
        self.name = name
        self.shape = None

    def distance_to(self, pos):
        """Compute the absolute distance between pos and a closest point on 
        the surface.

        signed_distance_to on the other hand returns a positive or negative 
        value depending on in which side the position is.  When this surface 
        defines a closed region in space, negative value means that the 
        position is inside.

        """
        return abs(self.shape.distance(pos))
  
    def __str__(self):
        return self.name


class PlanarSurface(Surface):
    """For example a membrane.

    Movement in 2D.

    """
    def __init__(self, name, origin, vector_x, vector_y, Lx, Ly, Lz=0):
        """Constructor.

        Docstring moved to add_cylindrical_surface in gfrdbase.py

        """
        Surface.__init__(self, name)

        unit_x = normalize(vector_x)
        unit_y = normalize(vector_y)
        assert numpy.dot(unit_x, unit_y) == 0.0
        # Orientation of surface is decided here.
        unit_z = numpy.cross(unit_x, unit_y)
        self.shape = Box(origin, unit_x, unit_y, unit_z, Lx, Ly, Lz) 
        self.DefaultSingle = PlanarSurfaceSingle
        self.DefaultPair = PlanarSurfacePair
        self.DefaultInteractionSingle = PlanarSurfaceInteraction

    def draw_bd_displacement(self, dt, D):
        r = math.sqrt(2.0 * D * dt)
        # Draw 2 numbers from normal distribution.
        x, y = myrandom.normal(0.0, r, 2)
        return x * self.shape.unit_x + y * self.shape.unit_y

    def random_vector(self, r):
        x, y = random_vector2D(r)
        return x * self.shape.unit_x + y * self.shape.unit_y

    def random_position(self):
        """Only uniform if vector_x and vector_y have same length.

        """
        return self.shape.position + myrandom.uniform(-1, 1) * self.shape.unit_x * self.shape.extent[0] + \
                             myrandom.uniform(-1, 1) * self.shape.unit_y * self.shape.extent[1]

    def minimal_distance_from_surface(self, radius):
        """A particle that is not on this surface has to be at least this far 
        away from the surface (measured from the origin of particle to the z = 
        0 plane of the surface).

        """
        return (self.shape.extent[2] + radius) * MINIMAL_SEPERATION_FACTOR

    def random_unbinding_site(self, pos, radius):
        return pos + myrandom.choice(-1, 1) * \
                     self.minimal_distance_from_surface(radius)  * self.shape.unit_z


class CylindricalSurface(Surface):
    """For example the DNA.

    Movement in 1D.

    """
    def __init__(self, name, origin, radius, orientation, size):
        """Constructor.

        Docstring moved to add_cylindrical_surface in gfrdbase.py

        """
        Surface.__init__(self, name)
        orientation = normalize(orientation)
        self.shape = Cylinder(origin, radius, orientation, size)
        self.DefaultSingle = CylindricalSurfaceSingle
        self.DefaultPair = CylindricalSurfacePair
        self.DefaultInteractionSingle = CylindricalSurfaceInteraction

    def draw_bd_displacement(self, dt, D):
        r = math.sqrt(2.0 * D * dt)
        # Draw 1 number from normal distribution.
        z = myrandom.normal(0.0, r, 1)
        return z * self.shape.unit_z

    def random_vector(self, r):
        return myrandom.choice(-1, 1) * r * self.shape.unit_z

    def random_position(self):
        return(self.shape.position + myrandom.uniform(-1, 1) *
                                     self.shape.unit_z * self.shape.size)

    def minimal_distance_from_surface(self, radius):
        """A particle that is not on this surface has to be at least this far 
        away from the surface (measured from the origin of the particle to the 
        the central axis of the surface.

        """
        return (self.shape.radius + radius) * MINIMAL_SEPERATION_FACTOR

    def random_unbinding_site(self, pos, radius):
        x, y = random_vector2D(self.minimal_distance_from_surface(radius))
        return pos + x * self.shape.unit_x + y * self.shape.unit_y


class CuboidalRegion(Surface):
    """
    A region that is (and can be) used for throwing in particles.

    Do not try to add this as a surface to your simulator, it won't work.

    It is also a Surface because particles for which no surface is 
    specified are tagged surface = default_surface, which is an instance of 
    this class. See gfrdbase.py.

    Movement in 3D.

    """
    def __init__(self, corner, size, name=''):
        """ Constructor.

        corner -- [x0, y0, z0] is one corner of the cube.
        size -- [sx, sy, sz] is the vector from the origin to the diagonal
        point.

        """
        Surface.__init__(self, name)
        self.size = numpy.array(size)
        Lx = size[0]
        Ly = size[1]
        Lz = size[2]
        self.shape = Box(corner + self.size / 2., [1, 0, 0], [0, 1, 0],
                         [0, 0, 1], Lx / 2., Ly / 2., Lz / 2.) 
        self.DefaultSingle = SphericalSingle
        self.DefaultPair = SphericalPair

    def draw_bd_displacement(self, dt, D):
        r = math.sqrt(2.0 * D * dt)
        # Draw 3 numbers from normal distribution.
        return myrandom.normal(0.0, r, 3)

    def random_vector(self, length):
        return random_vector(length)

    def signed_distance_to(self, pos):
        """Overrule signed_distance_to from Box. 
        Only for CuboidalRegions is cyclic_transpose 'pos' not needed.

        """
        raise RuntimeError('This method should not be used. Did you '
                           'accidently add this CuboidalRegion to the '
                           'surfacelist using s.add_surface()?')
        corner = self.origin - size / 2.
        dists = numpy.concatenate((corner - pos,
                                   corner + self.size - pos))
        absdists = numpy.abs(dists)
        i = numpy.argmin(absdists)
        return dists[i]

    def random_position(self):
        """Returns a random position equidistributed within
        the region in space defined by negative signed distance.
        See also signed_distance_to().

        """
        corner = self.shape.position - self.size / 2.
        return numpy.array([myrandom.uniform(corner[0], self.size[0]),
                            myrandom.uniform(corner[1], self.size[1]),
                            myrandom.uniform(corner[2], self.size[2])])


class SphericalSurface(Surface):
    '''
    origin -- = [x0, y0, z0] is the origin and
    radius -- the radius of the sphere.

    (x - x0)^2 + (y - y0)^2 + (z - z0)^2 = r^2
    '''
    def __init__(self, name, origin, radius):
        Surface.__init__(self, name)
        self.shape = Sphere(origin, radius)

    def random_position(self):
        pos = random_unit_vector_s()
        pos[0] *= self.radius
        return spherical_to_cartesian(pos)

    def set_params(self, origin, radius):
        self.origin = numpy.array(origin)
        self.radius = radius

    def get_params(self):
        return self.params
