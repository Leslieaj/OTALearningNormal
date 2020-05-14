import random
import math

from ota import Timedword
from otatable import Element
import interval


"""Equivalence query under PAC."""

def pac_equivalence_query(A, upperGuard, teacher, hypothesis, eqNum, epsilon, delta):
    """Equivalence query using random test cases."""
    # Number of tests in the current round.
    testNum = int((math.log(1 / delta) + math.log(2) * (eqNum + 1)) / epsilon)

    stateNum = len(teacher.locations)
    # print(testNum)
    for length in range(1, stateNum+2):
        ctx = None
        correct = 0
        i = 0
        # print(length)
        while i < testNum // stateNum:
            # Generate sample (delay-timed word) according to fixed distribution
            # sample = sampleGeneration(hypothesis.sigma, upperGuard, stateNum, length=length)
            sample = sampleGeneration2(A, upperGuard, length)

            # Evaluation of sample on the teacher, should be -1, 0, 1
            realValue = teacher.is_accepted_delay(sample.tws)
            
            # Evaluation of sample on the hypothesis, should be -1, 0, 1
            value = hypothesis.is_accepted_delay(sample.tws)

            # assert realValue in (-1, 0, 1) and value in (-1, 0, 1)
            # Compare the results
            i += 1
            if (realValue == 1 and value != 1) or (realValue != 1 and value == 1):
            # if (realValue != value):
                if ctx is None or sample.tws < ctx.tws:
                    ctx = sample
            else:
                correct += 1
    
        if ctx is not None:
            return False, ctx, length + correct / (testNum // stateNum)

    return True, None, stateNum+1


def sampleGeneration(inputs, upperGuard, stateNum, length=None):
    """Generate a sample."""
    sample = []
    if length is None:
        length = random.randint(1, stateNum)
    for i in range(length):
        input = inputs[random.randint(0, len(inputs) - 1)]
        time = random.randint(0, upperGuard * 2 + 1)
        if time % 2 == 0:
            time = time // 2
        else:
            time = time // 2 + 0.1
        temp = Timedword(input, time)
        sample.append(temp)
    return Element(sample, [])


def min_constraint_double(c):
    """
        Get the double of the minimal number in an interval.
        1. if the interval is empty, return None
        2. if [a, b$, return "2 * a".
        3. if (a, b$, return "2 * a + 1".
    """
    if c.isEmpty():
        return None
    if c.closed_min == True:
        return 2 * int(c.min_value)
    else:
        return 2 * int(c.min_value) + 1

def max_constraint_double(c, upperGuard):
    """
        Get the double of the maximal number in an interval.
        1. if the interval is empty, return None
        2. if $a, b], return "2 * b".
        3. if $a, b), return "2 * b - 1".
        4. if $a, +), return "2 * upperGuard + 1".
    """
    if c.isEmpty():
        return None
    if c.closed_max:
        return 2 * int(c.max_value)
    elif c.max_value == '+':
        return 2 * upperGuard + 1
    else:
        return 2 * int(c.max_value) - 1

def sampleDistribution(distr):
    s = sum(distr)
    if s == 0:
        return None
    a = random.randint(0, s-1)

    for i, n in enumerate(distr):
        if n > a:
            return i
        else:
            a -= n

def sampleGeneration_valid(teacher, upperGuard, length):
    """Generate a sample adapted to the given teacher."""
    # First produce a path (as a list of transitions) in the OTA
    path = []
    current_state = teacher.initstate_name
    for i in range(length):
        edges = []
        for tran in teacher.trans:
            if current_state == tran.source:
                edges.append(tran)
        edge = random.choice(edges)
        path.append(edge)
        current_state = edge.target

    # Next, figure out the minimum and maximum logical time.
    min_time, max_time = [], []
    for tran in path:
        assert len(tran.constraints) == 1
        min_time.append(min_constraint_double(tran.constraints[0]))
        max_time.append(max_constraint_double(tran.constraints[0], upperGuard))
    
    # For each transition, maintain a mapping from logical time to the
    # number of choices.
    weight = dict()
    for i in reversed(range(length)):
        tran = path[i]
        mn, mx = min_time[i], max_time[i]
        weight[i] = dict()
        if i == length-1 or tran.reset:
            for j in range(mn, mx+1):
                weight[i][j] = 1
        else:
            for j in range(mn, mx+1):
                weight[i][j] = 0
                for k, w in weight[i+1].items():
                    if k >= j:
                        weight[i][j] += w

    # Now sample according to the weights
    double_times = []
    cur_time = 0
    for i in range(length):
        start_time = max(min_time[i], cur_time)
        distr = []
        for j in range(start_time, max_time[i]+1):
            distr.append(weight[i][j])
        if sum(distr) == 0:
            return None  # sampling failed
        cur_time = sampleDistribution(distr) + start_time
        double_times.append(cur_time)
        if path[i].reset:
            cur_time = 0

    # Finally, obtain the resulting logical and delayed timed word.
    ltw = []
    for i in range(length):
        if double_times[i] % 2 == 0:
            time = double_times[i] // 2
        else:
            time = double_times[i] // 2 + 0.1
        ltw.append(Timedword(path[i].label, time))

    dtw = []
    for i in range(length):
        if i == 0 or path[i-1].reset:
            dtw.append(Timedword(path[i].label, ltw[i].time))
        else:
            dtw.append(Timedword(path[i].label, ltw[i].time - ltw[i-1].time))

    return Element(dtw, [])


def sampleGeneration2(teacher, upperGuard, length):
    if random.randint(0, 1) == 0:
        return sampleGeneration(teacher.sigma, upperGuard, len(teacher.locations), length)
    else:
        sample = None
        while sample is None:
            sample = sampleGeneration_valid(teacher, upperGuard, length)
        return sample


if __name__ == "__main__":
    random.seed(1)

    import sys
    from ota import buildOTA, buildAssistantOTA
    
    A = buildOTA(sys.argv[1], 's')
    AA = buildAssistantOTA(A, 's')
    A.show()
    for i in range(100):
        sample = sampleGeneration2(A, A.max_time_value(), 4)
        if sample:
            print(sample.tws)
