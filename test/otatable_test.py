#Unit tests for otatable.py

import unittest
import sys
sys.path.append('../')
from ota import buildAssistantOTA, buildOTA, ResetTimedword, Timedword
from otatable import init_table_normal, Element, guess_resets_in_suffixes

class EquivalenceTest(unittest.TestCase):
    def test_init_table_normal(self):
        A, _ = buildOTA('example6.json', 's')
        AA = buildAssistantOTA(A, 's')  # Assist
        #max_time_value = AA.max_time_value()
        sigma = AA.sigma

        tables = init_table_normal(sigma, AA)
        self.assertEqual(len(tables), 8)
        # for table, i in zip(tables, range(1, len(tables)+1)):
        #     print("------------"+ str(i)+"-----------------------")
        #     table.show()
    
    def test_is_closed(self):
        A, _ = buildOTA('example6.json', 's')
        AA = buildAssistantOTA(A, 's')  # Assist
        #max_time_value = AA.max_time_value()
        sigma = AA.sigma

        T1_tables = init_table_normal(sigma, AA)
        self.assertEqual(len(T1_tables), 8)
        #print("--------------------------------------------------")
        flag_closed, new_S, new_R, move = T1_tables[0].is_closed()
        self.assertEqual(flag_closed, False)
        self.assertEqual(new_S, [Element([],[0],[]), Element([ResetTimedword('a',0,False)],[-1],[])])
        self.assertEqual(new_R, [Element([ResetTimedword('b',0,False)],[-1],[]), Element([ResetTimedword('c',0,False)],[-1],[])])
        self.assertEqual(move, Element([ResetTimedword('a',0,False)],[-1],[]))

        flag_closed, new_S, new_R, move = T1_tables[5].is_closed()
        self.assertEqual(flag_closed, False)
        self.assertEqual(new_S, [Element([],[0],[]), Element([ResetTimedword('a',0,True)],[-1],[])])
        self.assertEqual(new_R, [Element([ResetTimedword('b',0,False)],[-1],[]), Element([ResetTimedword('c',0,True)],[-1],[])])
        self.assertEqual(move, Element([ResetTimedword('a',0,True)],[-1],[]))

    def test_guess_resets_in_suffixes(self):
        A, _ = buildOTA('example6.json', 's')
        AA = buildAssistantOTA(A, 's')  # Assist
        #max_time_value = AA.max_time_value()
        sigma = AA.sigma

        T1_tables = init_table_normal(sigma, AA)
        T1_table_0 = T1_tables[0]
        test_E = [[Timedword('a',2),Timedword('b',3),Timedword('a',1)],[Timedword('b',2),Timedword('a',4)],[Timedword('a',5)]]
        T1_table_0.E = test_E
        suffixes_resets = guess_resets_in_suffixes(T1_table_0)
        self.assertEqual(len(suffixes_resets), 64)
        self.assertEqual(len(suffixes_resets[22]), 3)
        for resets_situtation in suffixes_resets:
            print(resets_situtation)

if __name__ == "__main__":
    unittest.main()
