#The main file
import sys
import time
import copy

from ota import buildOTA, buildAssistantOTA
from otatable import init_table_normal, add_ctx_normal, make_closed, make_consistent
from hypothesis import to_fa, fa_to_ota, remove_sinklocation
from equivalence import equivalence_query_normal

def find_insert_place(tb, tblist):
    for table, index in zip(tblist, range(0,len(tblist))):
        if len(tb.S) < len(table.S):
            return index
    return len(tblist) - 1

def learn_ota(paras, debug_flag):
    #print("------------------A-----------------")
    A,_ = buildOTA(paras, 's')
    #A,_ = buildOTA("example.json", 's')
    #A.show()
    #print("------------------Assist-----------------")
    AA = buildAssistantOTA(A, 's')
    #AA.show()
    #print("--------------max value---------------------")
    max_time_value = A.max_time_value()
    #print(max_time_value)
    #print("--------------all regions---------------------")
    #regions = get_regions(max_time_value)
    # for r in regions:
    #     print(r.show())
    print("**************Start to learn ...*******************")
    print("---------------initial table-------------------")
    sigma = AA.sigma
    T1_tables = init_table_normal(sigma, AA)
    need_to_explore = []
    need_to_explore.extend(T1_tables)

    # List of existing counterexamples
    prev_ctx = []

    # Current number of tables
    t_number = 0
    start = time.time()
    equivalent = False
    eq_total_time = 0
    eq_number = 0
    target = None
    #while(true):
    while len(need_to_explore)>0:
        current_table = copy.deepcopy(need_to_explore.pop(0))
        t_number = t_number + 1
        if debug_flag:
            print("Table " + str(t_number) + " is as follow, %s has parent %s by %s" % (current_table.id, current_table.parent, current_table.reason))
            current_table.show()
            print("--------------------------------------------------")
        while equivalent == False:
            prepared = current_table.is_prepared(AA)
            while prepared == False:
                if t_number % 100 == 0:
                    print(t_number)
                flag_closed, new_S, new_R, move = current_table.is_closed()
                if flag_closed == False:
                    if debug_flag:
                        print("------------------make closed--------------------------")
                    temp_tables = make_closed(new_S, new_R, move, current_table, sigma, AA)
                    if len(temp_tables) > 0:
                        index_to_insert = find_insert_place(temp_tables[0], need_to_explore)
                        for i in range(0, len(temp_tables)):
                            need_to_explore.insert(index_to_insert+i, temp_tables[i])
                        # need_to_explore.extend(temp_tables)
                    current_table = copy.deepcopy(need_to_explore.pop(0))
                    t_number = t_number + 1
                    if debug_flag:
                        print("Table " + str(t_number) + " is as follow, %s has parent %s by %s" % (current_table.id, current_table.parent, current_table.reason))
                        current_table.show()
                        print("--------------------------------------------------")
                flag_consistent, new_a, new_e_index, reset_index_i, reset_index_j, reset_i, reset_j = current_table.is_consistent()
                if flag_consistent == False:
                    if debug_flag:
                        print("------------------make consistent--------------------------")
                    temp_tables = make_consistent(new_a, new_e_index, reset_index_i, reset_index_j, reset_i, reset_j, current_table, sigma, AA)
                    if len(temp_tables) > 0:
                        index_to_insert = find_insert_place(temp_tables[0], need_to_explore)
                        for i in range(0, len(temp_tables)):
                            need_to_explore.insert(index_to_insert+i, temp_tables[i])
                        # need_to_explore.extend(temp_tables)
                    current_table = copy.deepcopy(need_to_explore.pop(0))
                    t_number = t_number + 1
                    if debug_flag:
                        print("Table " + str(t_number) + " is as follow, %s has parent %s by %s" % (current_table.id, current_table.parent, current_table.reason))
                        current_table.show()
                        print("--------------------------------------------------")
                # current_table = copy.deepcopy(need_to_explore.pop(0))
                prepared = current_table.is_prepared(AA)
            
            fa_flag, fa, sink_name = to_fa(current_table, t_number)
            if t_number % 100 == 0:
                print(t_number)
            if fa_flag == False:
                #print(t_number)
                current_table = copy.deepcopy(need_to_explore.pop(0))
                t_number = t_number + 1
                if debug_flag:
                    print("Table " + str(t_number) + " is as follow, %s has parent %s by %s" % (current_table.id, current_table.parent, current_table.reason))
                    current_table.show()
                    print("--------------------------------------------------")
            else:
                h = fa_to_ota(fa, sink_name, sigma, t_number)
                target = copy.deepcopy(h)
                eq_start = time.time()
                equivalent, ctx = equivalence_query_normal(max_time_value, AA, h, prev_ctx)
                # Add counterexample to prev list
                if not equivalent and ctx not in prev_ctx:
                    prev_ctx.append(ctx)
                eq_end = time.time()
                eq_total_time = eq_total_time + eq_end - eq_start
                eq_number = eq_number + 1
                if equivalent == False:
                    temp_tables = add_ctx_normal(ctx.tws,current_table,AA)
                    if len(temp_tables) > 0:
                        index_to_insert = find_insert_place(temp_tables[0], need_to_explore)
                        for i in range(0, len(temp_tables)):
                            need_to_explore.insert(index_to_insert+i, temp_tables[i])
                        #need_to_explore.extend(temp_tables)
                    current_table = copy.deepcopy(need_to_explore.pop(0))
                    t_number = t_number + 1
                    if debug_flag:
                        print("Table " + str(t_number) + " is as follow, %s has parent %s by %s" % (current_table.id, current_table.parent, current_table.reason))
                        current_table.show()
                        print("--------------------------------------------------")
        end_learning = time.time()
        if target is None:
            print("Error! Learning Failed.")
            print("*******************Failed.***********************")
            return False
        else:
            print("Succeed! The learned OTA is as follows.")
            print("---------------------------------------------------")
            target.show()
            print("---------------------------------------------------")
            print("Total number of tables explored: " + str(t_number))
            print("Total number of tables to explore: " + str(len(need_to_explore)))
            print("Total time of learning: " + str(end_learning-start))
            return True

def main():
    learn_ota(sys.argv[1], debug_flag=False)


if __name__=='__main__':
	main()