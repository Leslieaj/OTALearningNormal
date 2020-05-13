import sys
import time
import math
import copy
import random

from ota import buildOTA, buildAssistantOTA
from otatable import init_table_normal, add_ctx_normal, make_closed, make_consistent
from hypothesis import to_fa, fa_to_ota, remove_sinklocation
from equivalence import equivalence_query_normal
from pac_equiv import pac_equivalence_query, sampleGeneration
from learnota import validateResult


def pac_learn_ota(paras, debug_flag):
    A = buildOTA(paras, 's')
    AA = buildAssistantOTA(A, 's')
    max_time_value = A.max_time_value()

    print("**************Start to learn ...*******************")
    print("---------------initial table-------------------")
    sigma = AA.sigma

    prev_ctx = []
    round_num = 0
    t_number = 0
    eq_total_time = 0.0
    eq_number = 0
    target = None
    start = time.time()

    def random_next_table(current_table):
        nonlocal t_number
        t_number += 1

        # First check if the table is closed
        flag_closed, new_S, new_R, move = current_table.is_closed()
        if not flag_closed:
            if debug_flag:
                print("------------------make closed--------------------------")
            temp_tables = make_closed(new_S, new_R, move, current_table, sigma, AA)
            if len(temp_tables) > 0:
                return random.choice(temp_tables)
            else:
                return 'failed'

        # If is closed, check if the table is consistent
        flag_consistent, new_a, new_e_index, reset_index_i, reset_index_j, reset_i, reset_j = current_table.is_consistent()
        if not flag_consistent:
            if debug_flag:
                print("------------------make consistent--------------------------")
            temp_tables = make_consistent(new_a, new_e_index, reset_index_i, reset_index_j, reset_i, reset_j, current_table, sigma, AA)
            if len(temp_tables) > 0:
                return random.choice(temp_tables)
            else:
                return 'failed'

        # If prepared, check conversion to FA
        fa_flag, fa, sink_name = to_fa(current_table, t_number)
        if not fa_flag:
            return 'failed'

        # Can convert to FA: convert to OTA and test equivalence
        h = fa_to_ota(fa, sink_name, sigma, t_number)
        eq_start = time.time()
        
        equivalent, ctx = True, None
        if prev_ctx is not None:
            for ctx in prev_ctx:
                teacher_res = AA.is_accepted_delay(ctx.tws)
                hypothesis_res = h.is_accepted_delay(ctx.tws)
                if teacher_res != hypothesis_res and hypothesis_res != -2:
                    equivalent, ctx = False, ctx

        if equivalent:
            # If equivalent, the current table is a candidate
            return 'candidate'
        else:
            # Otherwise, add counterexample
            temp_tables = add_ctx_normal(ctx.tws, current_table, AA)
            if len(temp_tables) > 0:
                return random.choice(temp_tables)
            else:
                return 'failed'

    init_tables = init_table_normal(sigma, AA)
    current_table = random.choice(init_tables)

    while True:
        failed = False
        while current_table.effective_len() < 15:
            print(current_table.effective_len())
            res = random_next_table(current_table)
            if res == 'failed':
                failed = True
                break
            elif res == 'candidate':
                break
            else:
                current_table = res

        if current_table.effective_len() >= 15:
            break

        if failed:
            return False

        print('ctx test:', current_table.effective_len())
        round_num += 1

        # If prepared, check conversion to FA
        fa_flag, fa, sink_name = to_fa(current_table, t_number)
        if not fa_flag:
            return False

        # Can convert to FA: convert to OTA and test equivalence
        h = fa_to_ota(fa, sink_name, sigma, t_number)
        eq_start = time.time()

        # equivalent, ctx = equivalence_query_normal(max_time_value, AA, h, prev_ctx)
        equivalent, ctx, _ = pac_equivalence_query(max_time_value, AA, h, round_num, 0.001, 0.001)

        # Add counterexample to prev list
        if not equivalent and ctx not in prev_ctx:
            prev_ctx.append(ctx)
        eq_end = time.time()
        eq_total_time = eq_total_time + eq_end - eq_start
        eq_number = eq_number + 1
        if not equivalent:
            temp_tables = add_ctx_normal(ctx.tws, current_table, AA)
            if len(temp_tables) > 0:
                current_table = random.choice(temp_tables)
            else:
                return False
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
        print("Total number of membership query: " + str(len(AA.membership_query)))
        print("Total number of membership query (no-cache): " + str(AA.mem_query_num))
        print("Total number of equivalence query: " + str(len(prev_ctx) + 1))
        print("Total number of equivalence query (no-cache): " + str(AA.equiv_query_num))
        print("Total number of tables explored: " + str(t_number))
        # print("Total number of tables to explore: " + str(need_to_explore.qsize()))
        print("Total time of learning: " + str(end_learning-start))
        return target_without_sink  


def main():
    target = None
    while not target:
        target = pac_learn_ota(sys.argv[1], debug_flag=False)

    if target:
        A = buildOTA(sys.argv[1], 's')
        AA = buildAssistantOTA(A, 's')
        validateResult(AA, target)


if __name__ == "__main__":
    random.seed(1)
    main()