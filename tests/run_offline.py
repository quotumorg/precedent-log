"""Run every test that does not require a network or provider call."""
import support
import unittest


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


if __name__ == '__main__':
    all_cases = list(cases(unittest.defaultTestLoader.discover(str(support.REPO / 'tests'))))
    offline = []
    for case in all_cases:
        if getattr(getattr(case, case._testMethodName), 'slow', False):
            print('NOT RUN (network/provider forbidden): ' + case.id(), flush=True)
        else:
            offline.append(case)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(offline))
    raise SystemExit(not result.wasSuccessful())
