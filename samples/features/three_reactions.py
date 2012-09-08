#!/usr/bin/env python

from simple_world import *
from simple_egfrd import *
from simple_gillespie import *
from three_reactions_model import *
import numpy

'''
To run this script:
PYTHONPATH=../../ python test.py

or, without terminal output and faster:
PYTHONPATH=../../ python -O test.py
'''


def run(SIMULATOR):
    # Number of particles.
    N_A = 200

    # For equilibrium, there should be 2 times less B than A particles.
    N_B = N_A / 2


    '''Define world.

    '''
    if SIMULATOR == 'EGFRD':
        matrix_size = int(((N_A + N_B) * 6) ** (1. / 3.))
        world = SimpleWorld(model, matrix_size)
        print 'matrix_size =', matrix_size
    elif SIMULATOR == 'Gillespie':
        world = SimpleWorld(model)


    '''Define simulator.

    A cube of dimension (L x L x L) is created, with periodic boundary 
    conditions.

    '''
    if SIMULATOR == 'EGFRD':
        simulator = SimpleEGFRDSimulator(world)
    else:
        simulator = SimpleGillespieSimulator(world)


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
    simulator.set_seed(SEED)

    # Make multis run 'BD_DT_FACTOR' times faster than normal.
    BD_DT_FACTOR = 1
    simulator.bd_dt_factor = BD_DT_FACTOR

    print 'N_A =', N_A
    print 'N_B =', N_B


    '''Add particles to world.

    '''
    world.place(A, [0, 0, 0])
    world.throw_in(A, N_A - 1)
    world.throw_in(B, N_B)


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
    aas = []
    bbs = []
    dt = 0.001
    dtprint = dt

    nextt = dt
    nextprint = dtprint

    i = 0
    while simulator.t < 1:
        if simulator.t > nextt:
            aas.append(world.get_population('A'))
            bbs.append(world.get_population('B'))
            nextt += dt

        if simulator.t > nextprint:
            print 'averages at t=%f: %.1f %.1f %d' % (simulator.t, numpy.average(aas), numpy.average(bbs), simulator.realsimulator.reaction_events)
            nextprint += dtprint

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

    simulator.print_report()
    simulator.stop(simulator.t)

    print 'averages = %.1f %.1f' % (numpy.average(aas), numpy.average(bbs))
    print 'std A =', numpy.std(aas)
    print 'std B =', numpy.std(bbs)

    print world.get_population()


'''Turn this module into a unit test case.

'''
import unittest
class TestTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_egfrd_test(self):
        print '############# Start EGFRD #############'
        run('EGFRD')

    def test_gillespie_test(self):
        print '############# Start Gillespie #############'
        #run('Gillespie')


if __name__ == "__main__":
    unittest.main()
