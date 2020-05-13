import random
import math

from ota import Timedword
from otatable import Element


"""Equivalence query under PAC."""

def pac_equivalence_query(upperGuard, teacher, hypothesis, eqNum, epsilon, delta):
    """Equivalence query using random test cases."""
    # Number of tests in the current round.
    testNum = int((math.log(1 / delta) + math.log(2) * (eqNum + 1)) / epsilon)

    stateNum = len(teacher.locations)
    # print(testNum)
    for length in range(1, stateNum+1):
        ctx = None
        correct = 0
        for i in range(testNum // stateNum):
            # Generate sample (delay-timed word) according to fixed distribution
            sample = sampleGeneration(hypothesis.sigma, upperGuard, stateNum, length=length)
            
            # Evaluation of sample on the teacher, should be -1, 0, 1
            realValue = teacher.is_accepted_delay(sample.tws)
            
            # Evaluation of sample on the hypothesis, should be -1, 0, 1
            value = hypothesis.is_accepted_delay(sample.tws)

            # assert realValue in (-1, 0, 1) and value in (-1, 0, 1)
            # Compare the results
            # if (realValue == 1 and value != 1) or (realValue != 1 and value == 1):
            if (realValue != value):
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
