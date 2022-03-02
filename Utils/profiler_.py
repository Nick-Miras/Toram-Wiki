import cProfile
import io
import pstats


def profile(f):
    def inner(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        ret_val = f(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sort_by = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
        ps.print_stats()
        print(s.getvalue())
        return ret_val

    return inner
