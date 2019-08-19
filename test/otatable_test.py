#Unit tests for otatable.py

import unittest
import sys
sys.path.append('../')
from ota import buildAssistantOTA, buildOTA
from otatable import init_table_normal

class EquivalenceTest(unittest.TestCase):
    def test_init_table_normal(self):
        A, _ = buildOTA('example6.json', 's')
        AA = buildAssistantOTA(A, 's')  # Assist
        max_time_value = AA.max_time_value()
        sigma = AA.sigma

        tables = init_table_normal(sigma, AA)
        self.assertEqual(len(tables), 8)
        for table, i in zip(tables, range(1, len(tables)+1)):
            print("------------"+ str(i)+"-----------------------")
            table.show()

if __name__ == "__main__":
    unittest.main()
