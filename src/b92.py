from qiskit import *
import numpy as np
from protocol import Protocol


class B92(Protocol):
    NAME = "B92"
    ENTANGLEMENT = False

    def encode_message(system):
        system._message = list(np.random.randint(2, size=system._n_bits))
        system._qubits = []
        for i in range(len(system._message)):
            qc = QuantumCircuit(1,1)

            if system._message[i] == 0:
                pass

            elif system._message[i] == 1:
                qc.h(0)

            system._qubits.append(qc)


    def measure_qubits(system):
        system._b_bases = list(np.random.randint(2, size=system._n_bits))
        backend = Aer.get_backend('aer_simulator')
        system._measured = []
        for q in range(len(system._qubits)):
            if system._qubits[q] is None:
                system._measured.append(None)
                continue

            if system._b_bases[q] == 0: # measuring in Z-basis
                system._qubits[q].measure(0,0)
            if system._b_bases[q] == 1: # measuring in X-basis
                system._qubits[q].h(0)
                system._qubits[q].measure(0,0)
            aer_sim = Aer.get_backend('aer_simulator')
            qobj = assemble(system._qubits[q], shots=1, memory=True)
            result = aer_sim.run(qobj).result()
            measured_bit = int(result.get_memory()[0])
            system._measured.append(measured_bit)


    def find_keys(system):
        system._a_key = []
        system._b_key = []
        for i, (base, measurement) in enumerate(zip(system._b_bases, system._measured)):
            if base == 0 and measurement == 1:
                system._a_key.append(system._message[i])
                system._b_key.append(1)
            elif base == 1 and measurement == 1:
                system._a_key.append(system._message[i])
                system._b_key.append(0)


    def cross_check(system, fraction):
        check_size = int(len(system._a_key)*fraction) + 1

        check_indexes = np.random.choice([i for i in range(len(system._a_key))], check_size)

        a_check = [system._a_key[i] for i in check_indexes]
        b_check = [system._b_key[i] for i in check_indexes]

        num_matches = len([i for i, j in zip(a_check, b_check) if i == j])

        system._a_key = [val for i, val in enumerate(system._a_key) if i not in check_indexes]
        system._b_key = [val for i, val in enumerate(system._b_key) if i not in check_indexes]

        return 1 - num_matches/check_size
    
    
    def eavesdrop(system):
        for qc in system._qubits:
            if np.random.random() < 0.5:
                if np.random.random() < 0.5:
                    qc.x(0)
                    qc.h(0)
                    qc.x(0)
                else:
                    qc.h(0)