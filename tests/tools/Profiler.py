import cProfile, pstats, io
from pstats import SortKey

pr = cProfile.Profile()


def start_profile():
    pr.enable()


def stop_profile():
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.TIME
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
