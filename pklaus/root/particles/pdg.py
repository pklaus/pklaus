import enum
from ROOT import TDatabasePDG

db = TDatabasePDG()
db.GetParticle(0) # initialize list
all_particles = list(db.ParticleList())
data = {p.GetName(): p.PdgCode() for p in all_particles}
ParticleID = enum.IntEnum('ParticleID', data)

if __name__ == "__main__":
    for pid in ParticleID:
        print(f"{pid.__class__.__name__}({pid.value}) == {pid.__class__.__name__}['{pid.name}']")
