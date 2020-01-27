import attr
import math

@attr.s
class Particle():

    #: eigentime of particle in fm/c
    t = attr.ib(type=float)
    #: x coordinate in fm
    rx = attr.ib(type=float)
    #: y coordinate in fm
    ry = attr.ib(type=float)
    #: z coordinate in fm
    rz = attr.ib(type=float)
    #: energy of particle in GeV
    E = attr.ib(type=float)
    #: x momentum component in GeV
    px = attr.ib(type=float)
    #: y momentum component in GeV
    py = attr.ib(type=float)
    #: z momentum component in GeV
    pz = attr.ib(type=float)
    #: mass of particle in GeV
    id = attr.ib(type=int, default=0)

class ExtendedParticle(Particle):
    @property
    def beta(self):
        return tuple(p_i/self.E for p_i in (self.px, self.py, self.pz))

    @property
    def theta(self):
        return 180. * math.atan2(math.sqrt(self.px**2 + self.py**2), self.pz) / math.pi

    @property
    def m0(self):
        #return float(self._properties[8]) # wrong?! column 8 is mass not invariant mass
        #return self.m / self.gamma
        return math.sqrt(self.E**2 + math.sqrt(self.px**2 + self.py**2 + self.pz**2))

    @property
    def gamma(self):
        return math.cosh(self.y)

    @property
    def m(self):
        return float(self._properties[8])

    @property
    def mT(self):
        return math.sqrt(self.m0**2 + self.px**2 + self.py**2)

    @property
    def y(self):
        """ rapidity """
        return .5 * math.log((self.E + self.pz)/(self.E - self.pz))

    def boost(self, boost_beta):
        """ Lorentz boost in positive z direction """
        boost_gamma = 1.0 / math.sqrt(1-boost_beta**2)
        t  = boost_gamma * (self.t  + boost_beta * self.rz)
        rz = boost_gamma * (self.rz + boost_beta * self.t)
        E  = boost_gamma * (self.E  + boost_beta * self.pz)
        pz = boost_gamma * (self.pz + boost_beta * self.E)
        self.t, self.rz, self.E, self.pz = t, rz, E, pz

def test():
    p = Particle(t=1, rx=1, ry=1, rz=1, E=10, px=1, py=1, pz=1)
    # upcast:
    p.__class__ = ExtendedParticle
    assert p.beta[2] == 0.1
    p.boost(boost_beta=0.99)
    assert p.beta[2] == 0.991810737033667
    # downcast:
    p.__class__ = Particle
    assert p.pz == 77.26805134590856

    p = Particle(0, 1, 1, 1, 10, 1, 1, 1)
    p.__class__ = ExtendedParticle
    #p.boost(0.9224028)

    def assert_almost_equal(t1, t2, allowed_rel_dev=1e-13):
        for i, (val1, val2) in enumerate(zip(t1, t2)):
            if val1 == val2: continue
            rel_dev = abs(val1 - val2) *2 / (val1 + val2)
            if rel_dev > allowed_rel_dev:
                raise AssertionError(f"tuple elements at index {i} are not identical within allowance: {val1} !~ {val2}")
    root_tuple = lambda rt, pE: (rt.T(), rt.X(), rt.Y(), rt.Z(), pE.E(), pE.Px(), pE.Py(), pE.Pz())
    particle_tuple = lambda p: (p.t, p.rx, p.ry, p.rz, p.E, p.px, p.py, p.pz)

    import copy
    p2 = copy.copy(p)
    assert_almost_equal(particle_tuple(p), particle_tuple(p2))
    p2.boost(0.1)
    p2.boost(-0.1)
    assert_almost_equal(particle_tuple(p), particle_tuple(p2))
    p2.boost(0.99)
    p2.boost(-0.99)
    p2.boost(0.99)
    p2.boost(-0.99)
    p2.boost(0.99)
    p2.boost(-0.99)
    p2.boost(0.99)
    p2.boost(-0.99)
    assert_almost_equal(particle_tuple(p), particle_tuple(p2))

    import ROOT
    rt = ROOT.TLorentzVector(p.rx, p.ry, p.rz, p.t)
    pE = ROOT.TLorentzVector(p.px, p.py, p.pz, p.E)

    assert_almost_equal(root_tuple(rt, pE), particle_tuple(p))

    rt.Boost(0, 0, 0.9224028)
    pE.Boost(0, 0, 0.9224028)
    p.boost(0.9224028)

    assert_almost_equal(root_tuple(rt, pE), particle_tuple(p))
    print('test passed')

if __name__ == "__main__":
    main()
