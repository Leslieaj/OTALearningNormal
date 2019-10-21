# OTALearning

A prototype on learning one-clock timed automata.

### Overview

This tool is dedicated to learning deterministic one-clock timed automata (DOTAs) which is a subclass of timed automata with only one clock. In 1987, Dana Angluin introduced the L* Algorithm for learning regular sets from queries and counterexamples. The tool implement an Angluin-style active learning algorithm on DOTAs. This branch is the normal teacher situation. The `master` and  `dev` branches are the smart teacher situation with and without the accelerating trick, respectively.

### Installation & Usage

#### Prerequisite

- Python 3.5.* (or high)


#### Installation

- Just download.

It's a pure Python program.  We have test it on Ubuntu 16.04 64bit with Python 3.5.2.

#### Usage

For example

```shell
python3 learnota.py experiments/example.json
```

- `learnota.py` is the main file of the program.

- The target DOTA is stored in a JSON file, in this example, `example.json` . The details are as follows.

  ```json
  {
    "name": "A",
    "l": ["1", "2"],
    "sigma": ["a", "b"],
    "tran": {
  	    "0": ["1", "a", "(1,3)", "n", "2"],
  	    "1": ["1", "b", "[0,+)", "r", "1"],
  	    "2": ["2", "b", "[2,4)", "r" "2"]
    },
    "init": "1",
    "accept": ["2"]
  }
  ```

  - "name" : the name of the target DOTA;
  - "s" : the set of the name of locations;
  - "sigma" : the alphabet;
  - "tran" : the set of transitions in the following form:
    - transition id : [name of the source location, action, guard, reset, name of the target location];
    - "+" in a guard means INFTY​;
    - "r" means resetting the clock, "n" otherwise.
- "init" : the name of initial location;
  - "accept" : the set of the name of accepting locations.
  
#### Output

- During the learning process, the following three numbers are printed, the number of the explored table, the number of the table to be explored, the number of effective row in $\bm{S}$ and $\bm{R}$.

- We do not print the current table in this case since there are so many explored table instances during the learning process.

- If we learn the target DOTA successfully, then the finial table instance, the learnt COTA, and the corresponding DOTA will be printed on the terminal. Additionally, the number of membership query (with and without cache), the number of equivalence query (with and without cache), the number of the explored table, the number of the table to be explored, and the learning time will also be given. 

- In the result file of each group of the randomly generated DOTAs, we records our experiment results. Each line records the results of one DOTA in the group. The meanings of the numbers in a line are learning time, location number, number of membership queries with cache, number of membership queries without cache, number of equivalence queries with cache, number of equivalence without cache, number of explored table instances, number of table instances to explore.

  |learning time|location number|mem_q (cahce)|mem_q(no-cache)|eq_q(cache)|eq_q(no-cache)|explored|to explore|effective row|
  
   
