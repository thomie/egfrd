#!/usr/bin/env python

import logging

import unittest

import numpy

import _gfrd

from egfrd import *

import model
import gfrdbase
import myrandom

log.setLevel(logging.WARNING)


class EGFRDSimulatorTestCase(unittest.TestCase):

    def setUp(self):
        self.m = model.ParticleModel(1e-5)
        self.S = model.Species('S', 2e-11, 5e-8)
        self.SS = model.Species('SS', 1e-12, 5e-9)
        self.A = model.Species('A', 0, 1e-8)
        self.B = model.Species('B', 2e-11, 5e-9)
        self.m.add_species_type(self.S)
        self.m.add_species_type(self.SS)
        self.m.add_species_type(self.A)
        self.m.add_species_type(self.B)
        self.m.set_all_repulsive()
        self.w = gfrdbase.create_world(self.m)
        self.nrw = _gfrd.NetworkRulesWrapper(self.m.network_rules)
        self.s = EGFRDSimulator(self.w, myrandom.rng, self.nrw)

    def tearDown(self):
        pass
    
    def test_instantiation(self):
        self.failIf(self.s == None)


    def test_one_particle(self):
        place_particle(self.s.world, self.S, [0.0,0.0,0.0])

        t = self.s.t
        for i in range(5):
            self.s.step()
        self.failIf(t == self.s.t)

    def test_two_particles(self):
        place_particle(self.s.world, self.S, [0.0,0.0,0.0])
        place_particle(self.s.world, self.S, [5e-6,5e-6,5e-6])

        t = self.s.t
        for i in range(5):
            self.s.step()
        self.failIf(t == self.s.t)

    def test_three_particles(self):
        place_particle(self.s.world, self.S, [0.0,0.0,0.0])
        place_particle(self.s.world, self.S, [5e-6,5e-6,5e-6])
        place_particle(self.s.world, self.S, [1e-7,1e-7,1e-7])

        t = self.s.t
        for i in range(5):
            self.s.step()
        self.failIf(t == self.s.t)


    def test_three_particles_in_contact(self):
        place_particle(self.s.world, self.S, [0.0,0.0,0.0])
        place_particle(self.s.world, self.S, [1e-7,0.0,0.0])

        # dummy
        place_particle(self.s.world, self.S, [2e-7,0.0,0.0])

        t = self.s.t
        for i in range(5):
            self.s.step()
        self.failIf(t == self.s.t)

    def test_four_particles_close(self):
        place_particle(self.s.world, self.SS, [2e-8,0.0,0.0])
        place_particle(self.s.world, self.SS, [3.003e-8,0.0,0.0])

        place_particle(self.s.world, self.SS, [0.994e-8-5e-10, 0.0, 0.0])

        t = self.s.t
        for i in range(10):
            self.s.step()
        self.failIf(t == self.s.t)

    def test_immobile_is_immobile(self):
        particleA = place_particle(self.s.world, self.A, [0.0,0.0,0.0])
        place_particle(self.s.world, self.B, [1.5000001e-8,0.0,0.0])

        initial_position = particleA[1].position

        for i in range(10):
            self.s.step()
        
        new_position = particleA[1].position
        dist = self.w.distance(initial_position, new_position)

        self.failIf(dist != 0, 'initial pos: %s,\tnew pos: %s' %
                    (initial_position, new_position))

    def test_pair_with_immobile(self):
        place_particle(self.s.world, self.A, [0.0, 0.0, 0.0])
        place_particle(self.s.world, self.B, [1.51e-8, 0.0, 0.0])

        for i in range(2):
            self.s.step()

    def test_pair_with_immobile_switched_order(self):
        place_particle(self.s.world, self.B, [1.51e-8, 0.0, 0.0])
        place_particle(self.s.world, self.A, [0.0, 0.0, 0.0])

        for i in range(2):
            self.s.step()


class EGFRDSimulatorTestCaseBase(unittest.TestCase):
    def setUpBase(self):
        self.L = 1e-6

        self.D = 1e-12
        self.radius = 5e-9

        self.m = model.ParticleModel(1.)

        self.A = model.Species('A', self.D, self.radius)
        self.B = model.Species('B', self.D, self.radius)
        self.C = model.Species('C', self.D, self.radius)

        self.kf_1 = 4000
        self.kf_2 = 5e-19
        self.kb_1 = 4000
        self.kb_2 = 4000

    def setUpPost(self):
        A = self.A
        B = self.B
        C = self.C

        self.m.add_species_type(A)
        self.m.add_species_type(B)
        self.m.add_species_type(C)

        self.w = create_world(self.m)
        self.nrw = _gfrd.NetworkRulesWrapper(self.m.network_rules)
        self.s = EGFRDSimulator(self.w, myrandom.rng, self.nrw)

        r = model.create_unimolecular_reaction_rule(A, B, self.kf_1)
        self.m.network_rules.add_reaction_rule(r)
        r = model.create_unimolecular_reaction_rule(B, A, self.kb_1)
        self.m.network_rules.add_reaction_rule(r)
        r = model.create_binding_reaction_rule(A, B, C, self.kf_2)
        self.m.network_rules.add_reaction_rule(r)
        r = model.create_unbinding_reaction_rule(C, A, B, self.kb_2)
        self.m.network_rules.add_reaction_rule(r)
        r = model.create_decay_reaction_rule(C, self.kb_1)
        self.m.network_rules.add_reaction_rule(r)

        throw_in_particles(self.w, A, 2)
        throw_in_particles(self.w, B, 2)

    def tearDown(self):
        pass


class EGFRDSimulatorCytosoleTestCase(EGFRDSimulatorTestCaseBase):
    def setUp(self):
        self.setUpBase()
        self.setUpPost() 

    def test_run(self):
        for i in range(10):
            self.s.step()


class EGFRDSimulatorMembraneTestCase(EGFRDSimulatorTestCaseBase):
    def setUp(self):
        self.setUpBase()

        m1 = model.create_planar_surface('m1',
                                         [0, 0, 0],
                                         [1, 0, 0],
                                         [0, 1, 0],
                                         self.L,
                                         self.L)

        self.m.add_structure(m1)

        self.A["surface"] = "m1"
        self.B["surface"] = "m1"
        self.C["surface"] = "m1"

        self.setUpPost()

    def test_run(self):
        for i in range(10):
            self.s.step()


class EGFRDSimulatorDnaTestCase(EGFRDSimulatorTestCaseBase):
    def setUp(self):
        self.setUpBase()

        radius = self.radius
        d = model.create_cylindrical_surface('d',
                                             [0, 0, 0],
                                             radius,
                                             [0, 1, 0],
                                             self.L)

        self.m.add_structure(d)

        self.A["surface"] = "d"
        self.B["surface"] = "d"
        self.C["surface"] = "d"

        self.setUpPost()

    def test_run(self):
        for i in range(10):
            self.s.step()

class DimerTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_one(self):
        import samples.dimer.dimer



if __name__ == "__main__":
    unittest.main()
