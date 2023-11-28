from qiskit import *
import numpy as np
from protocol import Protocol
import tools as Tools

class E91(Protocol):
    NAME = "E91"
    ENTANGLEMENT = True

    def encode_message(system):
        system._qubits = []
        for i in range(system._n_bits):
            qc = QuantumCircuit(2,2)
            
            # Create bell state
            qc.h(0)
            qc.cx(0,1)
            system._qubits.append(qc)

    
    def measure_qubits(system):
        system._a_bases = list(np.random.randint(3, size=system._n_bits)/8)
        system._b_bases = list(np.random.randint(3, size=system._n_bits)/8 + 1/8)
        backend = Aer.get_backend('aer_simulator')
        system._measured = []
        for q in range(len(system._qubits)):
            if system._qubits[q] is None:
                system._measured.append(None)
                continue

            if system._a_bases[q] == 0:
                system._qubits[q].measure(0,0)
            elif system._a_bases[q] == 1/8:
                system._qubits[q].ry(-2*np.pi/8, 0)
                system._qubits[q].measure(0,0) 
            elif system._a_bases[q] == 2/8:
                system._qubits[q].ry(-2*np.pi/4, 0)
                system._qubits[q].measure(0,0)
            
            if system._b_bases[q] == 1/8:
                system._qubits[q].ry(-2*np.pi/8, 1)
                system._qubits[q].measure(1,1)
            elif system._b_bases[q] == 2/8:
                system._qubits[q].ry(-2*np.pi/4, 1)
                system._qubits[q].measure(1,1)
            elif system._b_bases[q] == 3/8:
                system._qubits[q].ry(-2*3*np.pi/8, 1)
                system._qubits[q].measure(1,1)
            

            aer_sim = Aer.get_backend('aer_simulator')
            qobj = assemble(system._qubits[q], shots=1, memory=True)
            result = aer_sim.run(qobj).result()
            measured_bits = result.get_memory()
            measured_bits = [int(i) for i in measured_bits[0]]

            system._measured.append(measured_bits)

    
    def find_keys(system):
        system._a_key = []
        system._b_key = []
        for i, (a_base, b_base) in enumerate(zip(system._a_bases, system._b_bases)):
            if a_base == b_base and system._measured[i] is not None:
                system._a_key.append(system._measured[i][0])
                system._b_key.append(system._measured[i][1])
    
    
    def eavesdrop(system):
        for qc in system._qubits:
            qc.reset(0)
            qc.reset(1)

            if np.random.random() < 0.5:
                qc.x(0)
                qc.x(1)

    def test_statistic(system):
        def E_value(measurements):
            N11 = sum([1 for i in measurements if i == [1,1]])
            N00 = sum([1 for i in measurements if i == [0,0]])
            N01 = sum([1 for i in measurements if i == [0,1]])
            N10 = sum([1 for i in measurements if i == [1,0]])
            return (N11 + N00 - N01 - N10)/len(measurements)
        
        term1 = E_value([system._measured[i] for i, (a_base, b_base) in enumerate(zip(system._a_bases, system._b_bases)) if a_base == 0 and b_base == 1/8])
        term2 = E_value([system._measured[i] for i, (a_base, b_base) in enumerate(zip(system._a_bases, system._b_bases)) if a_base == 0 and b_base == 3/8])
        term3 = E_value([system._measured[i] for i, (a_base, b_base) in enumerate(zip(system._a_bases, system._b_bases)) if a_base == 1/4 and b_base == 1/8])
        term4 = E_value([system._measured[i] for i, (a_base, b_base) in enumerate(zip(system._a_bases, system._b_bases)) if a_base == 1/4 and b_base == 3/8])
        
        return term1 - term2 + term3 + term4