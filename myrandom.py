from _gfrd import RandomNumberGenerator
import numpy

__all__ = (
    'shuffle',
    'uniform',
    'normal',
    'seed',
    )

rng = RandomNumberGenerator.create()

def uniform(min=0.0, max=1.0, size=None):
     global rng
     return rng.uniform(min, max)

normal = rng.normal
seed = rng.seed

# By default seed is 0.
myseed = 0

# Choose seed at random.
#import random
#myseed = int(1e3 * random.random())

# Set seed.
seed(myseed)

def shuffle(seq):
    for i in reversed(range(0, len(seq))):
        j = rng.uniform_int(0, i)
        seq[i], seq[j] = seq[j], seq[i]

