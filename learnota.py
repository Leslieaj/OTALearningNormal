#The main file
import sys
import time
import math
import copy
import queue

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
    A = buildOTA(paras, 's')
    AA = buildAssistantOTA(A, 's')
    max_time_value = A.max_time_value()
    #print("--------------all regions---------------------")
    #regions = get_regions(max_time_value)
    # for r in regions:
    #     print(r.show())
    print("**************Start to learn ...*******************")
    print("---------------initial table-------------------")
    sigma = AA.sigma

    need_to_explore = queue.PriorityQueue()
    for table in init_table_normal(sigma, AA):
        need_to_explore.put((table.effective_len(), table))

    # List of existing counterexamples
    prev_ctx = []

    # Current number of tables
    t_number = 0
    start = time.time()
    equivalent = False
    eq_total_time = 0
    eq_number = 0
    target = None

    while True:
        depth, current_table = need_to_explore.get()
        t_number = t_number + 1

        if t_number % 1 == 0:
            print(t_number, need_to_explore.qsize(), current_table.effective_len())
        if debug_flag:
            print("Table " + str(t_number) + " is as follow, %s has parent %s by %s" % (current_table.id, current_table.parent, current_table.reason))
            current_table.show()
            print("--------------------------------------------------")

        # First check if the table is closed
        flag_closed, new_S, new_R, move = current_table.is_closed()
        if not flag_closed:
            if debug_flag:
                print("------------------make closed--------------------------")
            temp_tables = make_closed(new_S, new_R, move, current_table, sigma, AA)
            if len(temp_tables) > 0:
                depth += math.ceil(math.log(len(temp_tables), 2))
                for table in temp_tables:
                    need_to_explore.put((table.effective_len(), table))
            continue

        # If is closed, check if the table is consistent
        flag_consistent, new_a, new_e_index, reset_index_i, reset_index_j, reset_i, reset_j = current_table.is_consistent()
        if not flag_consistent:
            if debug_flag:
                print("------------------make consistent--------------------------")
            temp_tables = make_consistent(new_a, new_e_index, reset_index_i, reset_index_j, reset_i, reset_j, current_table, sigma, AA)
            if len(temp_tables) > 0:
                depth += math.ceil(math.log(len(temp_tables), 2))
                for table in temp_tables:
                    need_to_explore.put((table.effective_len(), table))
            continue
        
        # If prepared, check conversion to FA
        fa_flag, fa, sink_name = to_fa(current_table, t_number)
        if not fa_flag:
            continue

        # Can convert to FA: convert to OTA and test equivalence
        h = fa_to_ota(fa, sink_name, sigma, t_number)
        eq_start = time.time()
        equivalent, ctx = equivalence_query_normal(max_time_value, AA, h, prev_ctx)
        # Add counterexample to prev list
        if not equivalent and ctx not in prev_ctx:
            prev_ctx.append(ctx)
        eq_end = time.time()
        eq_total_time = eq_total_time + eq_end - eq_start
        eq_number = eq_number + 1
        if not equivalent:
            temp_tables = add_ctx_normal(ctx.tws, current_table, AA)
            if len(temp_tables) > 0:
                depth += math.ceil(math.log(len(temp_tables), 2))
                for table in temp_tables:
                    need_to_explore.put((table.effective_len(), table))
        else:
            target = copy.deepcopy(h)
            break

    end_learning = time.time()
    if target is None:
        print("Error! Learning Failed.")
        print("*******************Failed.***********************")
        return False
    else:
        print("Succeed! The learned OTA is as follows.")
        print("---------------------------------------------------")
        current_table.show()
        target.show()
        print("---------------------------------------------------")
        print("Total number of tables explored: " + str(t_number))
        print("Total number of tables to explore: " + str(need_to_explore.qsize()))
        print("Total time of learning: " + str(end_learning-start))
        return True

def main():
    learn_ota(sys.argv[1], debug_flag=False)


if __name__=='__main__':
	main()