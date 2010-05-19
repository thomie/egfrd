# Settings

READERS = True
PARTICLES = True
SHELLS = True
HELIX = True
SURFACES = True

PARTICLE_SCALE_FACTOR = 1
RESOLUTION = 18

from paraview.simple import *  # Should be listed first.
#from paraview.servermanager import *

def clear_pipeline():
    def name(proxy):
        return (type(proxy)).__name__

    def compare_glyphs_first(x,y):
        if name(x)[-5:] == 'Glyph':
            return -1
        if name(y)[-5:] == 'Glyph':
            return 1
        return cmp(x,y)

    for proxy in sorted(GetSources().itervalues(), compare_glyphs_first):
        # Hack to avoid 'Connection sink not found in the pipeline model' in 
        # Paraview 3.6.
        if hasattr(proxy, "Input") and proxy.Input:
            if isinstance(proxy.Input, servermanager.Proxy):
                proxy.Input = None
            else:
                proxy.Input[0] = None

        Delete(proxy)

clear_pipeline()


'''
def __MakeBlueToRedLT(min, max):
    # Define RGB points. These are tuples of 4 values. First one is
    # the scalar values, the other 3 the RGB values. 
    rgb_points = [min, 0, 0, 1, max, 1, 0, 0]
    return CreateLookupTable(RGBPoints=rgb_points, ColorSpace="HSV")
'''


def rename(proxy, name):
    # Hack to avoid 'Connection sink not found in the pipeline model' in 
    # Paraview 3.6.
    if hasattr(proxy, "Input") and proxy.Input:
        if isinstance(proxy.Input, servermanager.Proxy):
            input = proxy.Input
        else:
            input = proxy.Input[0]
        proxy.Input = None
    else:
        input = None

    # No need to unregister when using servermanager.sources/filters...(?)
    servermanager.UnRegister(proxy)
    servermanager.Register(proxy, registrationName=name)

    # Reset input.
    if input != None:
        if isinstance(input, servermanager.Proxy):
            proxy.Input = input
        else:
            proxy.Input[0] = input


def addPVDReader(file, name):
    reader = PVDReader(FileName=file)
    rename(reader, name)
    return reader

def add_glyph(data, type, name):
    glyph = Glyph(data, GlyphType=type)
    rename(glyph, name)
    return glyph

def add_extract_block(data, indices, name):
    block = ExtractBlock(data, BlockIndices=indices)
    rename(block, name)
    block.UpdatePipeline(); # Otherwise SetScaleFactor doesn't work. Otherwise TensorGlyph error.
    return block

def add_tensor_glyph(data, type, name):
    tensor_glyph = TensorGlyph(data, GlyphType=type)
    rename(tensor_glyph, name)
    return tensor_glyph



if READERS:
    # Read dynamic data.
    files = addPVDReader(simulation_data_directory + '/files.pvd', 'DynamicDataReader')

    # Read static data.
    static = addPVDReader(simulation_data_directory + '/static.pvd', 'StaticDataReader')




### DYNAMIC

if PARTICLES:
    # Particles.
    particles = add_extract_block(files, [2], 'ParticleData')
    particle = add_glyph(particles, 'Sphere', 'SphereGlyph')
    particle.SetScaleFactor = PARTICLE_SCALE_FACTOR
    particle.ScaleMode = 'scalar'

    display = GetDisplayProperties(particle)
    display.ColorArrayName = 'colors'

    range = particle.PointData[0].GetRange()
    display.LookupTable = MakeBlueToRedLT(range[0], range[1])


if SHELLS:
    # Spheres.
    spheres = add_extract_block(files, [4], 'SphereData')
    sphere = add_glyph(spheres, 'Sphere', 'SphereGlyph')
    sphere.GlyphType.ThetaResolution = RESOLUTION
    sphere.GlyphType.PhiResolution = RESOLUTION
    sphere.SetScaleFactor = 1
    sphere.ScaleMode = 'scalar'

    display = GetDisplayProperties(sphere)
    display.ColorArrayName = 'colors'
    display.Representation = 'Wireframe'
    display.Opacity = 0.5

    range = sphere.PointData[0].GetRange()
    lookup_table = MakeBlueToRedLT(range[0], range[1])
    display.LookupTable = lookup_table


    # Cylinders.
    cylinders = add_extract_block(files, [6], 'CylinderData')
    cylinder = add_tensor_glyph(cylinders, 'Cylinder', 'CylinderTensorGlyph')
    cylinder.GlyphType.Resolution = RESOLUTION

    display = GetDisplayProperties(cylinder)
    display.Representation = 'Wireframe'
    display.Opacity = 1.0

    # Todo.
    #range = cylinder.PointData[0].GetRange()
    #display.LookupTable = MakeBlueToRedLT(range[0], range[1])




### STATIC

# Helix.
if HELIX:
    # Todo.
    helix = ProgrammableSource()
    rename(helix, 'Helix')
    helix_file = open(paraview_scripts_directory + '/helix.py', 'r')
    helix.Script = helix_file.read()


if SURFACES:
    # Cylindrical surfaces.
    cylindrical_surfaces = add_extract_block(static, [2], 'CylindricalSurfaceData')
    cylindrical_surface = add_tensor_glyph(cylindrical_surfaces, 'Cylinder', 'CylinderTensorGlyph')
    # Todo. 
    #cylindrical_surface = TensorGlyphWithCustomSource(cylindrical_surfaces)
    #... Input=helix
    display = GetDisplayProperties(cylindrical_surface)
    display.Opacity = 0.2


    # Planar surfaces.
    planar_surfaces = add_extract_block(static, [4], 'PlanarSurfaceData')
    planar_surface = add_tensor_glyph(planar_surfaces, 'Box', 'BoxTensorGlyph')
    display = GetDisplayProperties(planar_surface)
    display.Representation = 'Wireframe'
    display.Opacity = 0.2


    # Cuboidal surfaces.
    cuboidal_surfaces = add_extract_block(static, [6], 'CuboidalSurfaceData')
    cuboidal_surface = add_tensor_glyph(cuboidal_surfaces, 'Box', 'BoxTensorGlyph')
    display = GetDisplayProperties(cuboidal_surface)
    display.Representation = 'Wireframe'
    display.Opacity = 1.0


# Initialize.
# Todo. Turn camera.
#SetActiveSource(cylindrical_surface)

renderer = Render()
renderer.Background = [0,0,0] # Black.
ResetCamera()

display = GetDisplayProperties(cylinder)

