from model import *
from utils import *
from dumper import *


'''Create model.

'''
# Size of simulation cube in meters.
L = 1e-6
m = ParticleModel(L)


'''Settings.

'''
# Radii in meters.
RADIUS_A = 5.0e-9
RADIUS_B = RADIUS_A

# Diffusion constants in meters^2 / second
D_A = 1.0e-12
D_B = D_A

# Bimolecular reaction rates in 'meters^3 per second'.
kon = 1.e-19

# Unimolecular reaction rates in 'per second'.
# For equilibrium, koff should be 3 / 2 * kon * [A].
koff = 45.

# Diffusion limited rate.
kD = k_D(2 * D_A, 2 * RADIUS_A) 

# Intrinsic reaction rates.
ka = k_a(kon, kD)
kd = k_d(koff, kon, kD)

assert kd == k_d_using_ka(koff, ka, kD)
assert kon == k_on(ka, kD)
assert feq(koff, k_off(kd, kon, kD))
assert feq(koff, k_off_using_ka(kd, ka, kD))

'''Define ParticleTypes.

'''
A = Species('A', D_A, RADIUS_A)
B = Species('B', D_B, RADIUS_B)


'''Add ParticleTypes (to specific Regions or Surfaces).

'''
m.add_species_type(A)
m.add_species_type(B)


'''Add reaction rules.

B     -> A + A
A + A -> B

'''
r1 = create_unbinding_reaction_rule(B, A, A, kd)
r2 = create_binding_reaction_rule(A, A, B, ka)
m.network_rules.add_reaction_rule(r1)
m.network_rules.add_reaction_rule(r2)


'''Output

'''
print 'L = ', L
print 'koff = ', koff
print 'kon = ', kon
print 'kD = ', kD
print 'kd = ', kd
print 'ka = ', ka
print 'kon / koff = ', kon / koff
print 'ka / kd = ', ka / kd

m.set_all_repulsive()
print dump_reaction_rules(m)

