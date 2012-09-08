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


def add_tensor_glyph(input, type, resolution=None, name=None, scale=None):
    if version == 4:
        if type == 'Cylinder':
            source = servermanager.sources.CylinderSource()
        elif type == 'Box':
            source = servermanager.sources.CubeSource()

        tensor_glyph = servermanager.filters.TensorGlyph(Input=input,
                                                         Source=source)

        tensor_glyph.SelectInputTensors = ['0', '', '', '', 'tensors']
        tensor_glyph.SelectInputScalars = ['1', '', '', '', 'colors']
        #tensor_glyph.SelectInputVectors = ['2', '', '', '', 'colors_as_vectors']
    else:
        tensor_glyph = servermanager.filters.TensorGlyph(Input=input,
                                                         GlyphType=type)

        if resolution != None:
            tensor_glyph.GlyphType.Resolution = resolution

        if scale != None:
            tensor_glyph.GlyphType.Radius *= scale

        tensor_glyph.Tensors = ['POINTS', 'tensors']
        tensor_glyph.Scalars = ['POINTS', 'colors']
        tensor_glyph.Vectors = ['POINTS', 'colors_as_vectors']

    if name != None:
        servermanager.Register(tensor_glyph, registrationName=name)
    else:
        servermanager.Register(tensor_glyph)

    return tensor_glyph


clear()

input = servermanager.sources.XMLUnstructuredGridReader(FileName='/storage1/miedema/code/simulations/example/data/run/files/cylinder_data50.vtu')
servermanager.Register(input)
input.UpdatePipeline()
input.UpdatePipelineInformation()
show(input)




glyph = add_tensor_glyph(input, 'Cylinder')
rep = show(glyph)




filter2 = servermanager.filters.ProgrammableFilter()
filter2.Input = glyph
filter2.Script = """
#print 'filter2: glyph'
pdi = self.GetInput()

pdata = pdi.GetPointData()

pdo = self.GetOutput()
pdo.ShallowCopy(pdi)

pdata = pdo.GetPointData()

scalars = pdata.GetArray(0)
scalars.SetName('colors')
#print 'filter2: pdata output'
#print pdata"""
servermanager.Register(filter2)

filter2.UpdatePipeline()
filter2.UpdatePipelineInformation()





set_color(glyph, rep)

rv.ResetCamera()
rv.StillRender()
