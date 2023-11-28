from qiskit import *
import numpy as np
from protocol import Protocol
import tools as Tools


class BB84(Protocol):
    NAME = "BB84"
    ENTANGLEMENT = False

    def encode_message(system):
        system._message = list(np.random.randint(2, size=system._n_bits))
        system._a_bases = list(np.random.randint(2, size=system._n_bits))
        system._qubits = []
        for i in range(len(system._message)):
            qc = QuantumCircuit(1,1)
            if system._a_bases[i] == 0: # Prepare qubits in Z-basis
                if system._message[i] == 0:
                    pass 
                else:
                    qc.x(0)
            else: # Prepare qubits in X-basis
                if system._message[i] == 0:
                    qc.h(0)
                else:
                    qc.x(0)
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
        for i, (a_base, b_base) in enumerate(zip(system._a_bases, system._b_bases)):
            if a_base == b_base and system._measured[i] is not None:
                system._a_key.append(system._message[i])
                system._b_key.append(system._measured[i])
    

    def eavesdrop(system):
        for qc in system._qubits:
            if np.random.random() < 0.5:
                if np.random.random() < 0.5:
                    qc.x(0)
                    qc.h(0)
                    qc.x(0)
                else:
                    qc.h(0)