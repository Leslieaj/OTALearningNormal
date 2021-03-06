#The main file
import sys
import time
import math
import copy
import queue
import random

from ota import buildOTA, buildAssistantOTA
from otatable import init_table_normal, add_ctx_normal, make_closed, make_consistent
from hypothesis import to_fa, fa_to_ota, remove_sinklocation
from equivalence import equivalence_query_normal
from pac_equiv import pac_equivalence_query, sampleGeneration, minimizeCounterexample


def find_insert_place(tb, tblist):
    for table, index in zip(tblist, range(0,len(tblist))):
        if len(tb.S) < len(table.S):
            return index
    return len(tblist) - 1

def learn_ota(paras, debug_flag):
    A = buildOTA(paras, 's')
    AA = buildAssistantOTA(A, 's')
    max_time_value = A.max_time_value()

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
    eq_total_time = 0
    eq_number = 0
    target = None

    while True:
        if need_to_explore.qsize() == 0:
            break
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
        
        # equivalent, ctx = equivalence_query_normal(max_time_value, AA, h, prev_ctx)
        equivalent, ctx = True, None
        if prev_ctx is not None:
            for ctx in prev_ctx:
                teacher_res = AA.is_accepted_delay(ctx.tws)
                hypothesis_res = h.is_accepted_delay(ctx.tws)
                if teacher_res != hypothesis_res and hypothesis_res != -2:
                    equivalent, ctx = False, ctx
                    ctx = minimizeCounterexample(AA, h, ctx)

        if equivalent:
            AA.equiv_query_num += 1
            equivalent, ctx, _ = pac_equivalence_query(A, max_time_value, AA, h, AA.equiv_query_num, 0.001, 0.001)

        if not equivalent:
            # remove_sinklocation(copy.deepcopy(h)).show()
            print(ctx.tws)

        # print(ratio)

        # Add counterexample to prev list
        if not equivalent and ctx not in prev_ctx:
            prev_ctx.append(ctx)
        eq_end = time.time()
        eq_total_time = eq_total_time + eq_end - eq_start
        eq_number = eq_number + 1
        if not equivalent:
            temp_tables = add_ctx_normal(ctx.tws, current_table, AA)
            if len(temp_tables) > 0:
                for table in temp_tables:
                    need_to_explore.put((table.effective_len(), table))
        else:
            target = copy.deepcopy(h)
            break

    end_learning = time.time()
    if target is None:
        print("---------------------------------------------------")
        print("Error! Learning Failed.")
        print("*******************Failed.***********************")
        return False
    else:
        print("---------------------------------------------------")
        print("Succeed! The learned OTA is as follows.")
        print("-------------Final table instance------------------")
        current_table.show()
        print("---------------Learned OTA-------------------------")
        target.show()
        print("---------------------------------------------------")
        print("Removing the sink location...")
        print()
        print("The learned One-clock Timed Automtaton: ")
        print()
        target_without_sink = remove_sinklocation(target)
        end_removesink = time.time()
        target_without_sink.show()
        print("---------------------------------------------------")
        print("Number of transitions in teacher: " + str(len(A.trans)))
        print("Total number of membership query: " + str(len(AA.membership_query)))
        # print("Total number of membership query (no-cache): " + str(AA.mem_query_num))
        # print("Total number of equivalence query: " + str(len(prev_ctx) + 1))
        print("Total number of equivalence query (no-cache): " + str(AA.equiv_query_num))
        print("Total number of tests: " + str(AA.test_query_num))
        print("Total number of tables explored: " + str(t_number))
        # print("Total number of tables to explore: " + str(need_to_explore.qsize()))
        print("Number of locations in learned table: " + str(len(target_without_sink.locations)))
        print("Total time of learning: " + str(end_learning-start))
        return target_without_sink  


def validateResult(teacher, hypothesis):
    inputs = teacher.sigma
    max_time_value = teacher.max_time_value()
    stateNum = len(teacher.locations)

    equivalent, _ = equivalence_query_normal(max_time_value, teacher, hypothesis)
    if equivalent:
        print("Completely correct!")
        return

    correct = 0
    for i in range(20000):
        sample = sampleGeneration(inputs, max_time_value, stateNum)
        realValue = teacher.is_accepted_delay(sample.tws)
        value = hypothesis.is_accepted_delay(sample.tws)
        if (realValue == 1 and value == 1) or (realValue != 1 and value != 1):
            correct += 1

    ratio = correct / 20000
    print('Ratio correct: %.4f' % ratio)
    return


def learn_ota_dfs(paras, depth, prev_ctx, debug_flag):
    A = buildOTA(paras, 's')
    AA = buildAssistantOTA(A, 's')
    max_time_value = A.max_time_value()

    sigma = AA.sigma

    # Current number of tables
    target = None
    t_number = 0

    def rec(current_table):
        """If solution is found, return target. Else, return None."""
        nonlocal t_number
        t_number += 1
        cur_depth = current_table.effective_len()
        if t_number % 10 == 0:
            print(t_number, cur_depth)

        if cur_depth > depth:
            return None

        # First check if the table is closed
        flag_closed, new_S, new_R, move = current_table.is_closed()
        if not flag_closed:
            temp_tables = make_closed(new_S, new_R, move, current_table, sigma, AA)
            for table in temp_tables:
                target = rec(table)
                if target is not None:
                    return target
            return None

        # If is closed, check if the table is consistent
        flag_consistent, new_a, new_e_index, reset_index_i, reset_index_j, reset_i, reset_j = current_table.is_consistent()
        if not flag_consistent:
            temp_tables = make_consistent(new_a, new_e_index, reset_index_i, reset_index_j, reset_i, reset_j, current_table, sigma, AA)
            for table in temp_tables:
                target = rec(table)
                if target is not None:
                    return target
            return None
        
        # If prepared, check conversion to FA
        fa_flag, fa, sink_name = to_fa(current_table, t_number)
        if not fa_flag:
            return None

        # Can convert to FA: convert to OTA and test equivalence
        h = fa_to_ota(fa, sink_name, sigma, t_number)
        equivalent, ctx = equivalence_query_normal(max_time_value, AA, h, prev_ctx)
        # Add counterexample to prev list
        if not equivalent and ctx not in prev_ctx:
            prev_ctx.append(ctx)
        if not equivalent:
            temp_tables = add_ctx_normal(ctx.tws, current_table, AA)
            for table in temp_tables:
                target = rec(table)
                if target is not None:
                    return target
            return None
        else:
            target = copy.deepcopy(h)
            return target


    tables = init_table_normal(sigma, AA)
    for table in tables:
        target = rec(table)
        if target is not None:
            return target, t_number

    return None, t_number

def learn_ota_idfs(paras, debug_flag):
    start = time.time()
    prev_ctx = []
    for depth in range(1, 40):
        target, t_number = learn_ota_dfs(paras, depth, prev_ctx, debug_flag)
        print("Depth:", str(depth), "Total number of tables explored:", str(t_number))
        if target is not None:
            break

    end_learning = time.time()
    if target is None:
        print("---------------------------------------------------")
        print("Error! Learning Failed.")
        print("*******************Failed.***********************")
        return False
    else:
        print("---------------------------------------------------")
        print("Succeed! The learned OTA is as follows.")
        print("-------------Final table instance------------------")
        # current_table.show()
        print("---------------Learned OTA-------------------------")
        # target.show()
        print("---------------------------------------------------")
        print("Removing the sink location...")
        print()
        print("The learned One-clock Timed Automtaton: ")
        print()
        target_without_sink = remove_sinklocation(target)
        target_without_sink.show()
        print("---------------------------------------------------")
        print("Total time of learning: " + str(end_learning-start))
        return True


def main():
    target = learn_ota(sys.argv[1], debug_flag=False)
    if target:
        A = buildOTA(sys.argv[1], 's')
        AA = buildAssistantOTA(A, 's')
        validateResult(AA, target)


if __name__ == '__main__':
    random.seed(3)
    main()