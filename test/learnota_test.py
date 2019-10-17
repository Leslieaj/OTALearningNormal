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
        learn_ota(os.getcwd() + '\\a.json', debug_flag=False)

# Result for a.json
# Total number of tables explored: 12160
# Total number of tables to explore: 15360
# Total time of learning: 903.7681005001068

# Total number of tables explored: 20608
# Total number of tables to explore: 15360
# Total time of learning: 364.96612524986267

if __name__ == "__main__":
    unittest.main()
