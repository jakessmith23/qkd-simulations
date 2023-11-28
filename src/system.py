from tools import Tools
import numpy as np
import tqdm
import time
from bb84 import BB84
from b92 import B92
from e91 import E91
from bbm92 import BBM92
import math

class System:
    def __init__(self, protocol, fiber_length, fiber_loss, perturb_probability, generation_rate, uncertainty_mean, detector_efficiency, source_efficiency):
        if protocol == "BB84":
            self._protocol = BB84
        elif protocol == "B92":
            self._protocol = B92
        elif protocol == "E91":
            self._protocol = E91
        elif protocol == "BBM92": 
            self._protocol = BBM92
        else:
            raise Exception("Invalid protocol")

        self._fiber_length = fiber_length
        self._fiber_loss = fiber_loss
        self._perturb_probability = perturb_probability
        self._generation_rate = generation_rate
        self._uncertainty_std = uncertainty_mean*np.sqrt(np.pi/2)
        self._detector_efficiency = detector_efficiency
        self._source_efficiency = source_efficiency

        self._loss_probability = 1 - (10 ** (-self._fiber_loss*self._fiber_length / 10))*self._detector_efficiency*self._source_efficiency

        self._n_bits = None
        self._message = None
        self._qubits = None
        self._measured = None
        self._a_bases = None
        self._b_bases = None
        self._a_key = None
        self._b_key = None

        self.__barrier_count = 0
        self.abort = False
    
    def encode(self):
        self._protocol.encode_message(self)
    
    def mess_with(self):
        for qc in self._qubits:
            if self._protocol.ENTANGLEMENT:
                if self._perturb_probability == 0 and self._uncertainty_std != 0:
                    random_angle = np.random.normal(0, self._uncertainty_std)
                    qc.ry(random_angle, 0)

                    random_angle = np.random.normal(0, self._uncertainty_std)
                    qc.ry(random_angle, 1)

                elif self._perturb_probability != 0 and self._uncertainty_std == 0:
                    if np.random.uniform() < self._perturb_probability:
                        random_angle = np.random.uniform(0, np.pi)
                        qc.ry(random_angle, 0)

                    if np.random.uniform() < self._perturb_probability:
                        random_angle = np.random.uniform(0, np.pi)
                        qc.ry(random_angle, 1)
                
                elif self._perturb_probability != 0 and self._uncertainty_std != 0:
                    if np.random.uniform() < self._perturb_probability:
                        random_angle = np.random.uniform(0, np.pi)
                        qc.ry(random_angle, 0)
                    else:
                        random_angle = np.random.normal(0, self._uncertainty_std)
                        qc.ry(random_angle, 0)

                    if np.random.uniform() < self._perturb_probability:
                        random_angle = np.random.uniform(0, np.pi)
                        qc.ry(random_angle, 1)
                    else:
                        random_angle = np.random.normal(0, self._uncertainty_std)
                        qc.ry(random_angle, 1)
            else:
                if self._perturb_probability == 0 and self._uncertainty_std != 0:
                    random_angle = np.random.normal(0, self._uncertainty_std)
                    qc.ry(random_angle, 0)

                elif self._perturb_probability != 0 and self._uncertainty_std == 0:
                    if np.random.uniform() < self._perturb_probability:
                        random_angle = np.random.uniform(0, np.pi)
                        qc.ry(random_angle, 0)
                
                elif self._perturb_probability != 0 and self._uncertainty_std != 0:
                    if np.random.uniform() < self._perturb_probability:
                        random_angle = np.random.uniform(0, np.pi)
                        qc.ry(random_angle, 0)
                    else:
                        random_angle = np.random.normal(0, self._uncertainty_std)
                        qc.ry(random_angle, 0)

    def measure(self):
        self._protocol.measure_qubits(self)

    def add_barrier(self):
        for qc in self._qubits:
            qc.barrier()
        self.__barrier_count += 1

    def eavesdrop(self):
        self._protocol.eavesdrop(self)


    def find_keys(self):
        self._protocol.find_keys(self)


    def cross_check(self, fraction):
        return self._protocol.cross_check(self, fraction)


    def show_sample(self):
        if self._protocol.ENTANGLEMENT:
            sample = np.random.choice(self._qubits, 5)
        else:
            sample = np.random.choice(self._qubits, 10)
        
        sample_filtered = [qc for qc in sample if qc is not None]
        
        Tools.draw_sample(sample_filtered, self.__barrier_count, self._protocol.ENTANGLEMENT)


    def simulate(self, n_bits, perturb=False, cross_check_fraction=None, losses=False, eavesdrop=False, add_uncertainty=False):
        self._n_bits = n_bits

        total_steps = 8

        progress_values = np.linspace(0, 100, total_steps + 1)
        currentPbarIndex = 0
        
        self.progress = progress_values[currentPbarIndex]
        currentPbarIndex += 1
        
        if self.abort:
            return None

        progress_bar = tqdm.tqdm(total=total_steps, desc="Simulating")

        actual_n_bits = self._n_bits

        if losses:
            self._n_bits = math.ceil(self._n_bits*(1-self._loss_probability))
        
        progress_bar.update(1)

        self.encode()
        self.add_barrier()
        progress_bar.update(1)

        if self.abort:
            return None

        self.progress = progress_values[currentPbarIndex]
        currentPbarIndex += 1
        
        if not perturb:
            self._perturb_probability = 0
        
        if not add_uncertainty:
            self._uncertainty_std = 0

        if perturb or add_uncertainty: 
            self.mess_with()
            self.add_barrier()

        progress_bar.update(1)
        progress_bar.update(1)

        if self.abort:
            return None
        
        self.progress = progress_values[currentPbarIndex]
        currentPbarIndex += 2

        if eavesdrop:
            self.eavesdrop()
            self.add_barrier()
        progress_bar.update(1)

        if self.abort:
            return None
        
        self.progress = progress_values[currentPbarIndex]
        currentPbarIndex += 1

        if self.abort:
            return None
        
        self.progress = progress_values[currentPbarIndex]
        currentPbarIndex += 1

        self.measure()
        progress_bar.update(1)

        if self.abort:
            return None
        
        self.progress = progress_values[currentPbarIndex]
        currentPbarIndex += 1

        self.find_keys()
        progress_bar.update(1)

        if self.abort:
            return None
        
        self.progress = progress_values[currentPbarIndex]
        currentPbarIndex += 1

        S = self._protocol.test_statistic(self)
        QBER = None

        if cross_check_fraction and len(self._a_key) > 0:
            QBER = self.cross_check(cross_check_fraction)
        
        progress_bar.update(1)

        if self.abort:
            return None
        
        self.progress = progress_values[currentPbarIndex]
        currentPbarIndex += 1

        progress_bar.close()
        print("Simulation complete!")

        self.results = {
            "Protocol": self._protocol.NAME,
            "Fiber length (km)": self._fiber_length,
            "Fiber loss (db/km)": self._fiber_loss,
            "Losses enabled": losses,
            "Calculated loss probability": self._loss_probability,
            "Qubit generation rate (Hz)": self._generation_rate,
            "Generation uncertainty std (rad)": self._uncertainty_std,
            "Uncertainty enabled": add_uncertainty,
            "Perturbations enabled": perturb,
            "Pertrubation probability": self._perturb_probability,
            "Number of bits sent": self._n_bits,
            "Key length": len(self._a_key),
            "Key rate": self._generation_rate * len(self._a_key) / actual_n_bits,
            "Cross check fraction": cross_check_fraction,
            "QBER": QBER,
            "S": S
        }

        return self.results
    
    def set_parameter(self, param_name, param_value):
        if param_name == "Fiber length":
            self._fiber_length = param_value
            self._loss_probability = 1 - (10 ** (-self._fiber_loss*self._fiber_length / 10))*self._detector_efficiency*self._source_efficiency
        elif param_name == "Fiber loss":
            self._fiber_loss = param_value
            self._loss_probability = 1 - (10 ** (-self._fiber_loss*self._fiber_length / 10))*self._detector_efficiency*self._source_efficiency
        elif param_name == "Perturb probability":
            self._perturb_probability = param_value/100
        elif param_name == "SOP mean deviation":
            self._uncertainty_std = param_value*np.sqrt(np.pi/2)
        elif param_name == "Source generation rate":
            self._generation_rate = param_value
        elif param_name == "Detector efficiency":
            self._detector_efficiency = param_value/100
            self._loss_probability = 1 - (10 ** (-self._fiber_loss*self._fiber_length / 10))*self._detector_efficiency*self._source_efficiency
        elif param_name == "Source efficiency":
            self._source_efficiency = param_value/100
            self._loss_probability = 1 - (10 ** (-self._fiber_loss*self._fiber_length / 10))*self._detector_efficiency*self._source_efficiency