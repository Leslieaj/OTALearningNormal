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
    target = None

    def random_one_step(current_table):
        """Find a random successor of the current table.

        Here a successor is defined to be the table after executing
        one make_closed, one make_consistent, or one add_ctx_normal
        on existing counterexamples.

        """
        nonlocal t_number

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
        t_number += 1
        fa_flag, fa, sink_name = to_fa(current_table, t_number)
        if not fa_flag:
            return 'failed'

        # Can convert to FA: convert to OTA and test equivalence
        h = fa_to_ota(fa, sink_name, sigma, t_number)
        
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

    def random_steps(current_table, max_len, cur_h, comparator=True):
        """Execute random_one_step until reaching a candidate.

        Here a candidate means a prepared table that agrees with teacher
        on all existing counterexamples.

        """
        nonlocal t_number

        while current_table.effective_len() < max_len:
            res = random_one_step(current_table)
            if res == 'failed':
                return 'failed'
            elif res == 'candidate':
                # Find shortest difference
                if cur_h is None or not comparator:
                    return current_table
                else:
                    t_number += 1
                    fa_flag, fa, sink_name = to_fa(current_table, t_number)
                    if not fa_flag:
                        return 'failed'
                    h = fa_to_ota(fa, sink_name, sigma, t_number)
                    equivalent, ctx = equivalence_query_normal(max_time_value, cur_h, h, None)
                    assert not equivalent
                    realValue = AA.is_accepted_delay(ctx.tws)
                    value = h.is_accepted_delay(ctx.tws)
                    if (realValue == 1 and value != 1) or (realValue != 1 and value == 1):
                        temp_tables = add_ctx_normal(ctx.tws, current_table, AA)
                        if len(temp_tables) > 0:
                            current_table = random.choice(temp_tables)
                        else:
                            return 'failed'
                    else:
                        return current_table
            else:
                current_table = res
        return 'failed'

    def single_search():
        """Single path search: at each step, pick a random successor."""
        nonlocal round_num

        init_tables = init_table_normal(sigma, AA)
        current_table = random.choice(init_tables)

        # Current hypothesis
        cur_h = None

        while True:
            round_num += 1
            current_table = random_steps(current_table, 15, cur_h, comparator=False)
            if current_table == 'failed':
                return None

            if current_table.effective_len() >= 15:
                return None

            print('ctx test:', current_table.effective_len())

            # If prepared, check conversion to FA
            fa_flag, fa, sink_name = to_fa(current_table, t_number)
            if not fa_flag:
                return None

            # Can convert to FA: convert to OTA and test equivalence
            cur_h = fa_to_ota(fa, sink_name, sigma, t_number)

            # equivalent, ctx = equivalence_query_normal(max_time_value, AA, cur_h, prev_ctx)
            equivalent, ctx, _ = pac_equivalence_query(A, max_time_value, AA, cur_h, round_num, 0.001, 0.001)
            if ctx:
                print(ctx.tws)

            # Add counterexample to prev list
            if not equivalent and ctx not in prev_ctx:
                prev_ctx.append(ctx)

            if not equivalent:
                temp_tables = add_ctx_normal(ctx.tws, current_table, AA)
                if len(temp_tables) > 0:
                    current_table = random.choice(temp_tables)
                else:
                    return None
            else:
                return current_table, cur_h


    def parallel_search():
        """Parallel search.
        
        Maintain a list of current tables (of size width). At each iteration,
        pick a number of random successors (of size expand_factor) to form
        the new list of tables. Sort the new list and pick the best 'width'
        tables for the next iteration.

        """ 
        nonlocal round_num, t_number

        init_tables = init_table_normal(sigma, AA)
        width = 15
        expand_factor = 2
        tables = []
        for i in range(width):
            tables.append(random.choice(init_tables))

        while round_num < 10:
            round_num += 1
            print(round_num)

            new_tables = []
            for i in range(min(len(tables), width)):
                for j in range(expand_factor):
                    if round_num == 1:
                        current_table, cur_h = tables[i], None
                    else:
                        current_table, cur_h, ctx = tables[i]
                        temp_tables = add_ctx_normal(ctx.tws, current_table, AA)
                        if len(temp_tables) > 0:
                            current_table = random.choice(temp_tables)
                        else:
                            continue

                    current_table = random_steps(current_table, 20, cur_h, comparator=False)
                    if current_table == 'failed':
                        continue

                    if current_table.effective_len() >= 20:
                        continue

                    # If prepared, check conversion to FA
                    t_number += 1
                    fa_flag, fa, sink_name = to_fa(current_table, t_number)
                    if not fa_flag:
                        continue

                    # Can convert to FA: convert to OTA and test equivalence
                    cur_h = fa_to_ota(fa, sink_name, sigma, t_number)

                    equivalent, ctx, sc = pac_equivalence_query(A, max_time_value, AA, cur_h, round_num, 0.001, 0.001)

                    if not equivalent:
                        new_tables.append((sc, current_table, copy.deepcopy(cur_h), ctx))
                    else:
                        return current_table, cur_h

            new_tables = sorted(new_tables, reverse=True)
            tables = []
            for sc, table, cur_h, ctx in new_tables:
                print(sc, table.effective_len())
                tables.append((table, cur_h, ctx))
                if len(tables) >= width:
                    break

        return None

    res = parallel_search()

    if res is None:
        print("---------------------------------------------------")
        print("Error! Learning Failed.")
        print("*******************Failed.***********************")
        return False
    else:
        current_table, target = res
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
        target_without_sink.show()
        print("---------------------------------------------------")
        print("Total number of membership query: " + str(len(AA.membership_query)))
        print("Total number of membership query (no-cache): " + str(AA.mem_query_num))
        print("Total number of equivalence query: " + str(len(prev_ctx) + 1))
        print("Total number of equivalence query (no-cache): " + str(AA.equiv_query_num))
        print("Total number of tables explored: " + str(t_number))
        # print("Total number of tables to explore: " + str(need_to_explore.qsize()))
        # print("Total time of learning: " + str(end_learning-start))
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
