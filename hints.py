"""Their own timetable, as a warm start and as the reproduction baseline. Labels are
normalised exactly as the derivation normalises them, so a lesson here is the same
lesson the instance asks for. In grades 11-12 a blank after a laboratory is the second
half of that double period, so it is placed too."""
from derive_all import RAW, read_csv, norm


def load(band, school, periods=None):
    periods = periods or school.periods
    rows, n = read_csv(RAW[band])
    out = {}
    for sec, (subs, _) in rows.items():
        if sec not in school.sections: continue
        last = None
        for i, lab in enumerate([norm(x) for x in subs]):
            d, p = divmod(i, periods)
            if p == 0: last = None
            if lab:
                last = lab
                if lab in school.req.get(sec, {}): out[sec, d, p] = lab
            elif last and "LAB" in last and last in school.req.get(sec, {}):
                out[sec, d, p] = last; last = None
            else:
                last = None
    return out
