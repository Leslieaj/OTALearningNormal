# Unit test for learnota

from pstats import Stats
import cProfile
import unittest
import sys, os
sys.path.append('../')
from learnota import learn_ota

class LearnOTATest(unittest.TestCase):
    def setUp(self):
        # self.pr = cProfile.Profile()
        # self.pr.enable()
        pass

    def tearDown(self):
        # p = Stats(self.pr)
        # p.strip_dirs()
        # p.sort_stats('cumtime')
        # p.print_stats()
        pass

    def testB(self):
        learn_ota(os.getcwd() + '\\example3.json', debug_flag=False)

# example3.json
# Total number of tables explored: 724
# Total number of tables to explore: 2752
# Total time of learning: 48.465362548828125

# Total number of tables explored: 384
# Total number of tables to explore: 372
# Total time of learning: 7.688438653945923


if __name__ == "__main__":
    unittest.main()
