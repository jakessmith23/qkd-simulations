import random
import math
import numpy as np


class Protocol:

    @staticmethod
    def encode_message(system):
        pass

    @staticmethod
    def measure_qubits(system):
        pass
    
    @staticmethod
    def find_keys(system):
        pass

    @staticmethod
    def cross_check(system, fraction):
        check_size = math.ceil(len(system._a_key)*fraction)

        check_indexes = random.sample([i for i in range(len(system._a_key))], check_size)

        a_check = [system._a_key[i] for i in check_indexes]
        b_check = [system._b_key[i] for i in check_indexes]

        num_matches = len([i for i, j in zip(a_check, b_check) if i == j])

        system._a_key = [val for i, val in enumerate(system._a_key) if i not in check_indexes]
        system._b_key = [val for i, val in enumerate(system._b_key) if i not in check_indexes]

        return 1 - num_matches/check_size

    @staticmethod
    def eavesdrop(system):
        pass

    @staticmethod
    def test_statistic(system):
        return None