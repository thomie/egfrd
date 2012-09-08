#!/usr/bin/env python

from features_model import *
from egfrd import *
from gillespie import *
import numpy

'''
To run this script:
PYTHONPATH=../../ python features.py

or, without terminal output and faster:
PYTHONPATH=../../ python -O features.py
'''


def run(SIMULATOR):
    # Number of particles.
    N_A = 350

    # For equilibrium, there should be 7 times less B than A particles.
    N_B = N_A / 7


    '''Define world.

    '''
    if SIMULATOR == 'EGFRD':
        matrix_size = int(((N_A + N_B) * 6) ** (1. / 3.))
        world = create_world(m, matrix_size)
        print 'matrix_size =', matrix_size


    '''Define simulator.

    A cube of dimension (L x L x L) is created, with periodic boundary 
    conditions.

    '''
    if SIMULATOR == 'EGFRD':
        simulator = EGFRDSimulator(world)
    else:
        simulator = GillespieSimulator(m, convert_rates=False)


    '''Toggles.

    '''
    LOGGER = None
    VTK_LOGGER = None

    #LOGGER = True
    #VTK_LOGGER = True


    '''Settings.

    '''
    # Random number generator seed.
    SEED = 0
    myrandom.seed(SEED)

    # Make multis run 'BD_DT_FACTOR' times faster than normal.
    BD_DT_FACTOR = 1
    simulator.bd_dt_factor = BD_DT_FACTOR

    N_A_BOX = N_A * 0.6
    N_B_BOX = N_B * 0.6

    # Todo.
    N_A_PLANE = N_A / 5
    N_B_PLANE = N_B / 5

    N_A_CYLINDER = N_A / 25
    N_B_CYLINDER = N_B / 25

    print 'N_A =', N_A
    print 'N_B =', N_B
    print 'N_A_BOX =', N_A_BOX
    print 'N_B_BOX =', N_B_BOX
    print 'N_A_PLANE =', N_A_PLANE
    print 'N_B_PLANE =', N_B_PLANE
    print 'N_A_CYLINDER =', N_A_CYLINDER
    print 'N_B_CYLINDER =', N_B_CYLINDER


    '''Add particles to world.

    '''
    if WORLD and not BOX:
        if SIMULATOR == 'EGFRD':
            place_particle(world, A, [0, 0, 0])
            throw_in_particles(world, A, N_A - 1)
            throw_in_particles(world, B, N_B)
        else:
            simulator.throw_in_particles(A, N_A)
            simulator.throw_in_particles(B, N_B)

    if PLANE1 and PLANE2 and BOX and not WORLD:
        # Add particles inside box only.
        throw_in_particles(world, Ab, N_A_BOX)
        throw_in_particles(world, Bb, N_B_BOX)

    if PLANE1:
        throw_in_particles(world, Ap1, N_A_PLANE)
        throw_in_particles(world, Bp1, N_B_PLANE)

    if PLANE2:
        pass

    if CYLINDER:
        throw_in_particles(world, Ac, N_A_CYLINDER)
        throw_in_particles(world, Bc, N_B_CYLINDER)


    '''Define loggers.

    '''
    if VTK_LOGGER == True:
        from vtklogger import VTKLogger
        # Write vtk files. See vtklogger.py. Use VTK or Paraview to 
        # visualize.  
        vtklogger = VTKLogger(simulator, 'data/run', extra_particle_step=True, 
                              buffer_size=20)

    if LOGGER == True:
        from logger import Logger
        # Write log files. See logger.py. Use visualizer.py to visualize.
        l = Logger('example')
        l.start(simulator)
        #l.set_particle_out_interval(1e-4) #1e-3)


    '''Run  simulation.

    '''
    averagea = get_number_of_particles(simulator, A)
    averageb = get_number_of_particles(simulator, B) 

    time_lastreaction = 0
    dt = 1.e-3
    nextt = dt

    i = 0
    while simulator.t < 10:
        if simulator.last_reaction != None: 
            na = get_number_of_particles(simulator, A)
            nb = get_number_of_particles(simulator, B)

            time_since_last_reaction = simulator.t - time_lastreaction

            averagea = (averagea * time_lastreaction +
                        na * time_since_last_reaction) / simulator.t

            averageb = (averageb * time_lastreaction +
                        nb * time_since_last_reaction) / simulator.t

            time_lastreaction = simulator.t

        if simulator.t > nextt:
            nextt += dt

            print '%.3f: %.1f %.1f' % (simulator.t, averagea, averageb)

        try:
            if VTK_LOGGER == True:
                vtklogger.log()
            if LOGGER == True and simulator.last_reaction:
                l.log(simulator, simulator.t)
            simulator.step()
        except Exception, message:
            print 'Exception at step = ', i
            print message
            if VTK_LOGGER == True:
                vtklogger.stop()
            simulator.print_report()
            raise

        i += 1

    if VTK_LOGGER == True:
        vtklogger.stop()

    simulator.stop(simulator.t)

    print '%.3f: %.1f %.1f' % (simulator.t, averagea, averageb)

    print dump_number_of_particles(simulator)

    print 'time end = ', simulator.t
    print 'time left = ', simulator.t - time_lastreaction

    simulator.print_report()


'''Turn this module into a unit test case.

'''
import unittest
class FeaturesTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_egfrd_features(self):
        print '############# Start EGFRD #############'
        #run('EGFRD')

    def test_gillespie_features(self):
        print '############# Start Gillespie #############'
        run('Gillespie')


if __name__ == "__main__":
    unittest.main()

