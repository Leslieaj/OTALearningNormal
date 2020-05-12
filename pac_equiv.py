import random
import math

from ota import Timedword
from otatable import Element


"""Equivalence query under PAC."""

def pac_equivalence_query(upperGuard, teacher, hypothesis, eqNum, epsilon, delta):
    """Equivalence query using random test cases."""
    # Number of tests in the current round.
    testNum = int((math.log(1 / delta) + math.log(2) * (eqNum + 1)) / epsilon)

    correct = 0
    print(testNum)
    for i in range(testNum):
        # Generate sample (delay-timed word) according to fixed distribution
        sample = sampleGeneration(hypothesis.sigma, upperGuard, len(teacher.locations))
        
        # Evaluation of sample on the teacher, should be -1, 0, 1
        realValue = teacher.is_accepted_delay(sample.tws)
        
        # Evaluation of sample on the hypothesis, should be -1, 0, 1
        value = hypothesis.is_accepted_delay(sample.tws)

        # Compare the results
        if (realValue == 1 and value == -1) or (realValue != 1 and value == 1):
            return False, sample, correct / testNum

    return True, None, 1.0


def sampleGeneration(inputs, upperGuard, stateNum):
    """Generate a sample."""
    sample = []
    length = math.ceil(random.gauss(1.4 * stateNum, 0.7 * stateNum))
    while length < 0:
        length = math.ceil(random.gauss(1.4 * stateNum, 0.7 * stateNum))
    for i in range(length):
        input = inputs[random.randint(0, len(inputs) - 1)]
        time = random.randint(0, upperGuard * 3) / 2
        if time > upperGuard:
            time = upperGuard
        temp = Timedword(input, time)
        sample.append(temp)
    return Element(sample, [])
