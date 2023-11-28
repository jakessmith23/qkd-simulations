import numpy as np
from qiskit import *
import matplotlib.pyplot as plt

class Tools:
    @staticmethod
    def random_binary_sequence(n):
        return list(np.random.randint(2, size=n))
    
    @staticmethod
    def draw(qc):
        qc.draw("mpl")
        plt.show()
    
    @staticmethod
    def draw_sample(qcs, total_n_barriers, entangled):
        sample_size = len(qcs)

        if entangled:
            sample_circuit = QuantumCircuit(2*sample_size, 2*sample_size)
        else:
            sample_circuit = QuantumCircuit(sample_size, sample_size)

        for barrier_number in range(1, total_n_barriers + 2):
            end = False

            for i, qc in enumerate(qcs):

                latest_barrier_index = 0
                
                barrier_count = 0

                for j, gate in enumerate(qc.data):

                    if gate[0].name == "barrier":

                        barrier_count += 1

                        if barrier_count == barrier_number:
                            qc_keep = qc.copy()

                            for k in range(j, len(qc.data)):
                                qc_keep.data.pop(-1)

                            for l in range(0, latest_barrier_index):
                                qc_keep.data.pop(0)
                            
                            if barrier_count > 1:
                                qc_keep.data.pop(0)

                            if entangled:
                                sample_circuit = sample_circuit.compose(qc_keep, qubits=[2*i, 2*i+1])
                            else:
                                sample_circuit = sample_circuit.compose(qc_keep, qubits=[i])
                            break

                        latest_barrier_index = j
                    
                    elif j == len(qc.data) - 1:

                        end = True

                        qc_keep = qc.copy()

                        for l in range(0, latest_barrier_index + 1):
                            qc_keep.data.pop(0)

                        if entangled:
                            sample_circuit = sample_circuit.compose(qc_keep, qubits=[2*i, 2*i+1])
                        else:
                            sample_circuit = sample_circuit.compose(qc_keep, qubits=[i])
                        
                        break
            
            if not end:
                sample_circuit.barrier()

        sample_circuit.draw("mpl", justify='left')
        
        plt.show()
    
    @staticmethod
    def bloch(qc):
        backend = Aer.get_backend("statevector_simulator")
        state = execute(qc, backend).result().get_statevector()
        plot_bloch_multivector(state)
        plt.show()