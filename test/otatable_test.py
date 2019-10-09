#Unit tests for otatable.py

import unittest
import sys,os
sys.path.append('../')
from ota import buildAssistantOTA, buildOTA, ResetTimedword, Timedword, dRTWs_to_lRTWs
from otatable import init_table_normal, Element, guess_resets_in_suffixes, guess_resets_in_newsuffix, normalize, prefixes, add_ctx_normal
from equivalence import equivalence_query_normal, guess_ctx_reset

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
        # for resets_situtation in suffixes_resets:
        #     print(resets_situtation)

    def test_guess_resets_in_newsuffix(self):
        A, _ = buildOTA('example6.json', 's')
        AA = buildAssistantOTA(A, 's')  # Assist
        #max_time_value = AA.max_time_value()
        sigma = AA.sigma

        T1_tables = init_table_normal(sigma, AA)
        T1_table_0 = T1_tables[0]
        test_E = [[Timedword('a',2),Timedword('b',3),Timedword('a',1)],[Timedword('b',2),Timedword('a',4)]]
        T1_table_0.E = test_E
        suffixes_resets = guess_resets_in_newsuffix(T1_table_0)
        self.assertEqual(len(suffixes_resets),256)
        self.assertEqual(len(suffixes_resets[34]), 4)
        self.assertEqual(suffixes_resets[1],[[True,True],[True,True],[True,True],[True,False]])

        test_E = [[Timedword('a',2),Timedword('b',3),Timedword('a',1)]]
        T1_table_0.E = test_E
        suffixes_resets = guess_resets_in_newsuffix(T1_table_0)
        self.assertEqual(len(suffixes_resets),4096)
        self.assertEqual(len(suffixes_resets[34]), 4)
        self.assertEqual(suffixes_resets[1],[[True,True,True],[True,True,True],[True,True,True],[True,True,False]])

    def test_add_ctx_normal(self):
        experiments_path = os.path.dirname(os.getcwd())+"/experiments/"
        A, _ = buildOTA(experiments_path+'example3.json', 's')
        AA = buildAssistantOTA(A, 's')
        sigma = AA.sigma
        max_time_value = AA.max_time_value()

        H, _ = buildOTA(experiments_path+'example3_1.json', 'q')
        HH = buildAssistantOTA(H, 'q')

        # AA.show()
        # print("------------------------------")
        # HH.show()
        # print("------------------------------")
        # H.show()
        flag, ctx = equivalence_query_normal(max_time_value,AA,HH)
        print("-------------ctx-----------------")
        print(ctx.tws)
        ctxs = guess_ctx_reset(ctx.tws)
        print(len(ctxs))
        for rtws in ctxs:
            print(rtws)
        print("-------------local tws-----------------")
        for ctx in ctxs:
            local_tws = dRTWs_to_lRTWs(ctx)
            normalize(local_tws)
            #if check_guessed_reset(local_tws, table) == True:
            print(ctx)
            print(local_tws)
            pref = prefixes(local_tws)
            for tws in pref:
                print(tws)
            print("-------------------")
        
        # T1_tables = init_table_normal(sigma, AA)
        # T1_table_0 = T1_tables[0]
        # test_E = [[Timedword('b',2),Timedword('a',4)],[Timedword('a',5)]]
        # T1_table_0.E = test_E
        # T1_table_0.show()
        # print("----------------------------------------")
        # tables = add_ctx_normal(ctx, T1_table_0, AA)
        # self.assertEqual(len(tables),65536)
        # tables[0].show()
        # tables[1].show()
        # tables[2].show()
        # tables[100].show()
        # tables[4095].show()
        # for table in tables:
        #     table.show()
        #     print("---------------------")

        T1_tables = init_table_normal(sigma, AA)
        T1_table_0 = T1_tables[0]
        test_E = [[Timedword('b',2),Timedword('a',4)]]
        T1_table_0.E = test_E
        T1_table_0.show()
        print("----------------------------------------")
        tables = add_ctx_normal(ctx, T1_table_0, AA)
        #self.assertEqual(len(tables),4096)
        print(len(tables))
        tables[0].show()
        tables[1].show()
        tables[2].show()
        tables[100].show()
        #tables[4095].show()

if __name__ == "__main__":
    unittest.main()
