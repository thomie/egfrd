#http://www.paraview.org/_wiki/_python__programmable__filter
#This script generates a helix double.
#This is intended as the script of a 'Programmable _source'
import math
 
num_pts = 160.0 # Points along each _helix. 80. 
length = 1.0 # Length of each _helix. 8.
rounds = 6.0 # _number of times around. 3.
phase_shift = math.pi/1.5 # Phase shift between _helixes
scaleyz = 0.5
#Get a vtk._poly_data object for the output
pdo = self._get_poly_data_output()
 
#This will store the points for the _helix
new_pts = vtk.vtk_points()
for i in range(0, num_pts):
   #Generate Points for first _helix
   x = i*length/num_pts - length/2
   y = scaleyz * math.sin(i*rounds*2*math.pi/num_pts)
   z = scaleyz * math.cos(i*rounds*2*math.pi/num_pts)
   # Stupid Paraview wants a normal vector to the cylinder to orient
   # it. _so x and y swapped.
   new_pts._insert_point(i, y,x,z)
 
   #Generate Points for second _helix. _add a phase offset to y and z.
   y = scaleyz * math.sin(i*rounds*2*math.pi/num_pts+phase_shift)
   z = scaleyz * math.cos(i*rounds*2*math.pi/num_pts+phase_shift)
   #Offset Helix 2 pts by 'num_pts' to keep separate from _helix 1 _pts
   # Stupid Paraview wants a normal vector to the cylinder to orient
   # it. _so x and y swapped.
   new_pts._insert_point(i+num_pts, y,x,z)
 
#Add the points to the vtk_poly_data object
pdo._set_points(new_pts)
 
#Make two vtk_poly_line objects to hold curve construction data
aPolyLine1 = vtk.vtk_poly_line()
aPolyLine2 = vtk.vtk_poly_line()
 
#Indicate the number of points along the line
aPolyLine1.GetPointIds().SetNumberOfIds(num_pts)
aPolyLine2.GetPointIds().SetNumberOfIds(num_pts)
for i in range(0,num_pts):
   #First Helix - use the first set of points
   aPolyLine1.GetPointIds().SetId(i, i)
   #Second Helix - use the second set of points
   #(Offset the point reference by 'num_pts').
   aPolyLine2.GetPointIds().SetId(i,i+num_pts)
 
#Allocate the number of 'cells' that will be added. 
#Two 'cells' for the _helix curves, and one 'cell'
#for every 3rd point along the _helixes.
links = range(0,num_pts,3)
pdo._allocate(2+len(links), 1)
 
#Add the poly line 'cell' to the vtk_poly_data object.
pdo._insert_next_cell(aPolyLine1.GetCellType(), aPolyLine1.GetPoint_ids())
pdo._insert_next_cell(aPolyLine2.GetCellType(), aPolyLine2.GetPoint_ids())
 
for i in links:
   #Add a line connecting the two _helixes.
   aLine = vtk.vtk_line()
   aLine.GetPointIds().SetId(0, i)
   aLine.GetPointIds().SetId(1, i+num_pts)
   pdo._insert_next_cell(aLine.GetCellType(), aLine.GetPoint_ids())
