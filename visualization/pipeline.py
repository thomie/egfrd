READERS   = False
PARTICLES = False
SHELLS    = False
HELIX     = False
SURFACES  = False

# Settings
READERS   = True
PARTICLES = True
#SHELLS    = True
#HELIX     = True
#SURFACES  = True

PARTICLE_SCALE_FACTOR = 4
RESOLUTION = 18

import sys
sys.path.append(paraview_scripts_directory)
import helpers

import paraview

from paraview import servermanager

try:
    paraview.compatibility
    paraview.compatibility.minor = 4
    if servermanager.ActiveConnection:
        # 6: paraview 3.6.
        # 5: as much as possible compatible with paraview 3.4.
        version = 5
    else:
        # Hack. I don't remember why this is needed.
        version = 4
except:
    version = 4


def clear():
    def name(proxy):
        return (type(proxy)).__name__

    def compare_glyphs_first(x,y):
        if name(x)[-5:] == 'Glyph':
            return -1
        if name(y)[-5:] == 'Glyph':
            return 1
        return cmp(x,y)

    for proxy in sorted(helpers.GetSources().itervalues(), 
                        compare_glyphs_first):
        helpers.Delete(proxy, version) # Delete in simple.py needs hack in 3.6.


def register(proxy, name):
    # Hack to avoid 'Connection sink not found in the pipeline model' in 
    '''
    if hasattr(proxy, "Input"):
        input = proxy.Input
    else:
        input = None
    '''

    # No need to unregister when using servermanager.sources/filters.
    # Or: no need to register when using simple.Glyph() etc.
    #servermanager.UnRegister(proxy)
    servermanager.Register(proxy, registrationName=name)

    '''
    # Reset input.
    if input != None:
        proxy.Input = input
    '''


def addPVDReader(file, name):
    reader = servermanager.sources.PVDReader(FileName=file)
    register(reader, name)
    return reader

def add_extract_block(data, indices, name):
    block = servermanager.filters.ExtractBlock(Input=data, 
                                               BlockIndices=indices)
    register(block, name)
    # Otherwise SetScaleFactor doesn't work. Otherwise TensorGlyph error.
    block.UpdatePipeline();
    return block


def add_tensor_glyph(data, type, name):
    tensor_glyph = servermanager.filters.TensorGlyph(Input=data, 
                                                     GlyphType=type)
    #tensor_glyph = vtk.vtkTensorGlyph(data, GlyphType=type)
    register(tensor_glyph, name)
    return tensor_glyph


print 'clear pipeline'
clear()
print 'build pipeline'


if not servermanager.ActiveConnection:
    if version == 4 or version == 5:
        # Paraview 3.4.
        # Paraview 3.6 mimicking 3.4.
        servermanager.Connect()
    else:
        # Paraview 3.6.
        helpers.Connect()

try:
    views = servermanager.GetRenderViews()
    if len(views) > 0:
        print 'reuse render view'
        renModule = views[0]
    else:
        print 'new render view'
        renModule = servermanager.CreateRenderView()
except KeyError:
    renModule = servermanager.CreateRenderView()


if READERS:
    # Read dynamic data.
    files = addPVDReader(simulation_data_directory + '/files.pvd', 'DynamicDataReader')

    # Read static data.
    static = addPVDReader(simulation_data_directory + '/static.pvd', 'StaticDataReader')


if PARTICLES:
    # Particles.
    particles = add_extract_block(files, [2], 'ParticleData')
    if version == 4:
        # Paraview 3.4.
        source = servermanager.sources.SphereSource()
        particle = servermanager.filters.Glyph(Input=particles, 
                                               Source=source)
        particle.SetScaleMode = 0
    else:
        # Paraview 3.6 mimicking 3.4.
        # Paraview 3.6.
        particle = servermanager.filters.Glyph(Input=particles, 
                                               GlyphType='Sphere')
        helpers.UpdatePipeline(proxy=particle);
        particle.ScaleMode = 'scalar'

    register(particle, 'SphereGlyph')

    particle.SetScaleFactor = PARTICLE_SCALE_FACTOR

    if version == 4 or version == 5:
        # Paraview 3.4.
        # Paraview 3.6 mimicking 3.4.
        display = helpers.GetDisplayProperties(particle, renModule)
        #display = helpers.Show(particle, version=version)
        #display = servermanager.CreateRepresentation(particle, renModule)
        #display.SelectionVisibility = 1
    else:
        # Paraview 3.6.
        display = helpers.Show(particle)

    '''
    display.ColorArrayName = 'colors'

    # Todo.
    #range = particle.PointData[0].GetRange()
    #display.LookupTable = helpers.MakeBlueToRedLT(range[0], range[1])
    '''


if SHELLS:
    # Spheres.
    spheres = add_extract_block(files, [4], 'SphereData')
    if version == 4:
        # Paraview 3.4.
        source = servermanager.sources.SphereSource()
        sphere = servermanager.filters.Glyph(Input=spheres, Source=source)
        sphere.SetScaleMode = 0
        sphere.ThetaResolution = RESOLUTION
        sphere.PhiResolution = RESOLUTION
    else:
        # Paraview 3.6 mimicking 3.4.
        # Paraview 3.6.
        sphere = servermanager.filters.Glyph(Input=spheres, 
                                             GlyphType='Sphere')
        sphere.ScaleMode = 'scalar'
        sphere.GlyphType.ThetaResolution = RESOLUTION
        sphere.GlyphType.PhiResolution = RESOLUTION

    register(sphere, 'SphereGlyph')

    sphere.SetScaleFactor = 1

    if version == 4 or version == 5:
        # Paraview 3.4.
        # Paraview 3.6 mimicking 3.4.
        display = servermanager.CreateRepresentation(sphere, renModule)
        display.SelectionVisibility = 1
    else:
        # Paraview 3.6.
        display = helpers.Show(sphere)
        #display = helpers.GetDisplayProperties(sphere)

    display.ColorArrayName = 'colors'
    display.Representation = 'Wireframe'
    display.Opacity = 0.5

    # Todo.
    #range = sphere.PointData[0].GetRange()
    #lookup_table = helpers.MakeBlueToRedLT(range[0], range[1])
    #display.LookupTable = lookup_table

    ''' Todo.
    # Cylinders.
    cylinders = add_extract_block(files, [6], 'CylinderData')
    cylinder = add_tensor_glyph(cylinders, 'Cylinder', 
                                'CylinderTensorGlyph')
    #helpers.Show(cylinder)
    # Todo.
    #cylinder.GlyphType.Resolution = RESOLUTION

    display = helpers.GetDisplayProperties(cylinder)
    display.Representation = 'Wireframe'
    display.Opacity = 1.0

    # Todo.
    #range = cylinder.PointData[0].GetRange()
    #display.LookupTable = helpers.MakeBlueToRedLT(range[0], range[1])
    '''


if HELIX:
    helix_file = open(paraview_scripts_directory + '/helix.py', 'r')
    if version == 4 or version == 5:
        # Paraview 3.4.
        # Paraview 3.6 mimicking 3.4.
        #helix = ProgrammableFilter()
        #helix.Script = helix_file.read()
        #servermanager.Register(helix) # Needed, or register.
        pass
    else:
        # Paraview 3.6.
        # Todo. Scale it.
        helix = servermanager.sources.ProgrammableSource()
        helix.Script = helix_file.read()
        register(helix, 'Helix')
        helpers.Show(helix)


if SURFACES and version == 6:
    # Cylindrical surfaces.
    cylindrical_surfaces = add_extract_block(static, [2], 
                                             'CylindricalSurfaceData')
    cylindrical_surface = add_tensor_glyph(cylindrical_surfaces, 
                                           'Cylinder', 
                                           'CylinderTensorGlyph')
    #helpers.Show(cylindrical_surface)
    # Todo. 
    #cylindrical_surface = TensorGlyphWithCustomSource(cylindrical_surfaces)
    #... Input=helix
    display = helpers.GetDisplayProperties(cylindrical_surface)
    display.Opacity = 0.2


    # Planar surfaces.
    planar_surfaces = add_extract_block(static, [4], 'PlanarSurfaceData')
    planar_surface = add_tensor_glyph(planar_surfaces, 'Box', 
                                      'BoxTensorGlyph')
    #helpers.Show(planar_surface)
    display = helpers.GetDisplayProperties(planar_surface)
    display.Representation = 'Wireframe'
    display.Opacity = 0.2


    # Cuboidal surfaces.
    cuboidal_surfaces = add_extract_block(static, [6], 
                                          'CuboidalSurfaceData')
    cuboidal_surface = add_tensor_glyph(cuboidal_surfaces, 'Box', 
                                        'BoxTensorGlyph')
    #helpers.Show(cuboidal_surface)
    display = helpers.GetDisplayProperties(cuboidal_surface)
    display.Representation = 'Wireframe'
    display.Opacity = 1.0


# Todo. Turn camera.
#SetActiveSource(cylindrical_surface)

# Todo.
if version == 4 or version == 5:
    # Paraview 3.4.
    # Paraview 3.6 mimicking 3.4.
    renModule.StillRender()
    helpers.ResetCamera(renModule)
else:
    # Paraview 3.6.
    renderer = helpers.Render()
    renderer.Background = [0,0,0] # Black.
    helpers.ResetCamera()

#display = helpers.GetDisplayProperties(cylinder)




