from paraview import servermanager

# Detect version.
try:
    from paraview import simple
    version = 6
except ImportError:
    version = 4
print 'version =', version

rv = servermanager.GetRenderViews()[0]

# Taken from simple.py (ParaView 3.6).
class _funcs_internals:
    "Internal class."
    first_render = True
    view_counter = 0
    rep_counter = 0

def show(proxy):
    if version == 4:
        # Adapted from Show in simple.py (ParaView 3.6).
        rep = servermanager.CreateRepresentation(proxy, rv)
        servermanager.ProxyManager().RegisterProxy("representations", \
          "my_representation%d" % _funcs_internals.rep_counter, rep)
        _funcs_internals.rep_counter += 1
    else:
        rep = simple.Show(proxy)

    #rep.Visibility = 1
    #rep.SelectionVisibility = 1
    return rep

def clear():
    def name(proxy):
        return (type(proxy)).__name__

    def cmp_tubes_filters_glyphs(x,y):
        if name(x) == 'GenerateTubes':
            return -1
        elif name(y) == 'GenerateTubes':
            return 1
        if name(x) == 'ProgrammableFilter':
            return -1
        elif name(y) == 'ProgrammableFilter':
            return 1
        elif name(x) == 'Glyph' or name(x)[:11] == 'TensorGlyph':
            return -1
        elif name(y) == 'Glyph' or name(y)[:11] == 'TensorGlyph':
            return 1
        return cmp(x,y)

    pxm = servermanager.ProxyManager()
    for proxy in pxm.GetProxiesInGroup('lookup_tables').itervalues():
        servermanager.UnRegister(proxy)

    if version == 4:
        for proxy in sorted(pxm.GetProxiesInGroup('sources').itervalues(),
                            cmp_tubes_filters_glyphs):
            if hasattr(proxy, "Input"):
                # Avoid 'Connection sink not found in the pipeline model'.
                proxy.Input = None
            servermanager.UnRegister(proxy)
        for proxy in pxm.GetProxiesInGroup('representations').itervalues():
            servermanager.UnRegister(proxy)

        rv.Representations = []
    else:
        for proxy in sorted(simple.GetSources().itervalues(), 
                            cmp_tubes_filters_glyphs):
            if hasattr(proxy, "Input"):
                # Avoid 'Connection sink not found in the pipeline model'.
                proxy.Input = None
            if hasattr(proxy, "GlyphType"):
                # Avoid 'Connection sink not found in the pipeline model'.
                proxy.GlyphType = None
            simple.Delete(proxy)

    rv.ResetCamera()
    rv.StillRender()


def set_color(proxy, rep):
    rep.ColorArrayName = 'colors'

    if version == 4:
        rep.ColorAttributeType = 0 # point data

        # Adapted from MakeBlueToRedLT in simple.py (ParaView 3.6).
        def MakeBlueToRedLT(min, max):
            lt = servermanager.rendering.PVLookupTable()
            servermanager.Register(lt)

            # Define RGB points. These are tuples of 4 values. First one is
            # the scalar values, the other 3 the RGB values. 
            rgbPoints = [min, 0, 0, 1, max, 1, 0, 0]
            lt.RGBPoints = rgbPoints
            lt.ColorSpace = "HSV"

            return lt

        pdi = proxy.GetDataInformation().GetPointDataInformation()
        range = pdi.GetArrayInformation('colors').GetComponentRange(0)
        lt = MakeBlueToRedLT(range[0], range[1])
    else:
        range = proxy.PointData.GetArray('colors').GetRange()
        lt = simple.MakeBlueToRedLT(range[0], range[1])

    rep.LookupTable = lt

def add_sphere_glyph(input, resolution=None, name=None):
    if version == 4:
        source = servermanager.sources.SphereSource()
        if resolution != None:
            source.ThetaResolution = resolution
            source.PhiResolution = resolution
        glyph = servermanager.filters.Glyph(Input=input, 
                                            Source=source)

        # Prevent "selected proxy value not in the list".
        # http://www.paraview.org/pipermail/paraview/2008-March/007416.html
        sourceProperty = glyph.GetProperty("Source")
        domain = sourceProperty.GetDomain("proxy_list");
        domain.AddProxy(source.SMProxy)

        glyph.SetScaleMode = 0
        glyph.SelectInputScalars = ['0', '0', '0', '0', 'colors2']
        glyph.SelectInputVectors = ['1', '0', '0', '0', 'vector2']

    else:
        glyph = servermanager.filters.Glyph(Input=input, 
                                            GlyphType='Sphere')
        glyph.ScaleMode = 'scalar'

        if resolution != None:
            glyph.GlyphType.ThetaResolution = resolution
            glyph.GlyphType.PhiResolution = resolution

    glyph.SetScaleFactor = 1

    if name != None:
        servermanager.Register(glyph, registrationName=name)
    else:
        servermanager.Register(glyph)

    return glyph


clear()

input = servermanager.sources.XMLUnstructuredGridReader(FileName='/storage1/miedema/code/simulations/example/data/run/files/particle_data50.vtu')
servermanager.Register(input)
input.UpdatePipeline()
input.UpdatePipelineInformation()
show(input)





glyph = add_sphere_glyph(input)
rep = show(glyph)




'''

filter1 = servermanager.filters.ProgrammableFilter()
filter1.Input = input
filter1.Script = """
print 'filter1: input'
pdi = self.GetInput()

pdata = pdi.GetPointData()
print 'filter1: pdata input'
print pdata

pdo = self.GetOutput()
pdo.ShallowCopy(pdi)

pdata = pdo.GetPointData()

scalars = pdata.GetArray(0)
scalars.SetName('array0')
print 'filter1: pdata output'
print pdata"""
servermanager.Register(filter1)

filter1.UpdatePipeline()
filter1.UpdatePipelineInformation()


'''


filter2 = servermanager.filters.ProgrammableFilter()
filter2.Input = glyph
filter2.Script = """
print 'filter2: glyph'
pdi = self.GetInput()

pdata = pdi.GetPointData()
print 'filter2: pdata input'
print pdata

pdo = self.GetOutput()
pdo.ShallowCopy(pdi)

pdata = pdo.GetPointData()

scalars = pdata.GetArray(0)
scalars.SetName('array0')
print 'filter2: pdata output'
print pdata"""
servermanager.Register(filter2)

filter2.UpdatePipeline()
filter2.UpdatePipelineInformation()





#set_color(glyph, rep)

rv.ResetCamera()
rv.StillRender()
