from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
from gui import Ui_Window
from system import System
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from threading import Thread

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

class Main():
    def __init__(self, ui):
        self._ui = ui
        self._system = None
        self._view_system = None

        pixmap = QtGui.QPixmap("resources/sample_plot.png")
        self._ui.multiPlot.setPixmap(pixmap)
        self._ui.multiPlot.repaint()

        self.set_signals()

        self.run_thread = None

    def set_signals(self):
        self._ui.runButton.clicked.connect(self.run_clicked)
        self._ui.multiRunButton.clicked.connect(self.multiple_run_clicked)
        self._ui.protocolDropdown.currentIndexChanged.connect(self.protocol_changed)
        self._ui.xParameter.currentIndexChanged.connect(self.x_param_changed)
        self._ui.viewSample.clicked.connect(self.viewSampleClicked)
        self._ui.abortButton.clicked.connect(self.abortClicked)
        self._ui.abortButtonSingle.clicked.connect(self.abortClicked)
    
    def abortClicked(self):
        self.timer.stop()

        if self._system:
            self._system.abort = True
            self.run_thread.join()
        
        plt.close()

    def x_param_changed(self):
        param_name = self._ui.xParameter.currentText()

        if param_name == "Fiber length":
            self._ui.startValue.setSuffix(" km")
            self._ui.endValue.setSuffix(" km")
        elif param_name == "Fiber loss":
            self._ui.startValue.setSuffix(" dB/km")
            self._ui.endValue.setSuffix(" dB/km")
            self._ui.lossesEnabled.setChecked(True)
        elif param_name == "Perturb probability":
            self._ui.startValue.setSuffix(" %")
            self._ui.endValue.setSuffix(" %")
            self._ui.perturbationsEnabled.setChecked(True)
        elif param_name == "SOP mean deviation":
            self._ui.startValue.setSuffix(" rad")
            self._ui.endValue.setSuffix(" rad")
            self._ui.generationUncertaintyEnabled.setChecked(True)
        elif param_name == "Cross check fraction":
            self._ui.startValue.setSuffix(" %")
            self._ui.endValue.setSuffix(" %")
        elif param_name == "Source generation rate":
            self._ui.startValue.setSuffix(" MHz")
            self._ui.endValue.setSuffix(" MHz")
        elif param_name == "Detector efficiency":
            self._ui.startValue.setSuffix(" %")
            self._ui.endValue.setSuffix(" %")
            self._ui.lossesEnabled.setChecked(True)
        elif param_name == "Source efficiency":
            self._ui.startValue.setSuffix(" %")
            self._ui.endValue.setSuffix(" %")
            self._ui.lossesEnabled.setChecked(True)
    
    def protocol_changed(self):
        protocol = self._ui.protocolDropdown.currentText()

        self._ui.yParameter.clear()

        if protocol == "E91":
            self._ui.yParameter.addItems(["Key length", "Key rate", "QBER", "S"])
        else:
            self._ui.yParameter.addItems(["Key length", "Key rate", "QBER"])

    def run_clicked(self):
        if self.run_thread:
            if self.run_thread.is_alive():
                return

        self.read_system_parameters()
        self.run_simulation()
    
    def multiple_run_clicked(self):
        if self.run_thread:
            if self.run_thread.is_alive():
                return
        
        plt.figure()
        
        self.read_system_parameters()
        self.run_multiple_simulations()
    
    def viewSampleClicked(self):
        if self.run_thread:
            if self.run_thread.is_alive():
                return

        if self._view_system:
            self._view_system.show_sample()
    
    def read_system_parameters(self):
        protocol = self._ui.protocolDropdown.currentText()
        fiber_length = self._ui.fiberLength.value()
        fiber_loss = self._ui.fiberLoss.value()
        perturb_prob = self._ui.perturbProbability.value()/100
        generation_rate = self._ui.generationRate.value()*1e6
        generation_uncertainty_mean = self._ui.generationUncertainty.value()
        detector_efficiency = self._ui.detectorLoss.value()/100
        source_efficiency = self._ui.sourceEfficiency.value()/100

        self._system = System(
            protocol=protocol, 
            fiber_length=fiber_length, 
            fiber_loss=fiber_loss, 
            perturb_probability=perturb_prob, 
            generation_rate=generation_rate, 
            uncertainty_mean=generation_uncertainty_mean,
            detector_efficiency=detector_efficiency,
            source_efficiency=source_efficiency
        )
    
    def run_simulation(self):
        perturb = self._ui.perturbationsEnabled.isChecked()
        losses = self._ui.lossesEnabled.isChecked()
        cross_check_fraction = self._ui.crossCheckFraction.value()/100
        num_qubits = self._ui.numberOfQubits.value()
        eavesdrop = self._ui.eavesdroppingEnabled.isChecked()
        add_uncertainty = self._ui.generationUncertaintyEnabled.isChecked()

        self._system.progress = 0

        results = None

        self.run_thread = Thread(target = self._system.simulate, args = (num_qubits, perturb, cross_check_fraction, losses, eavesdrop, add_uncertainty))
        self.run_thread.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.single_simulation_progress_check_callback)
        self.timer.start(100)
    
    def single_simulation_progress_check_callback(self):
        self._ui.progressBar.setValue(round(self._system.progress))
        if self._system.progress == 100:
            results = self._system.results

            if results is None:
                return

            self._ui.finalKeyLength.setText(str(results["Key length"]))
            self._ui.keyGenerationRate.setText(str(round(results["Key rate"], 2)) + " Hz")
            self._ui.QBER.setText(str(round(results["QBER"]*100, 2)) + " %" if results["QBER"] is not None else "None")
            self._ui.S.setText(str(round(results["S"], 2)) if results["S"] else "None")
            self._ui.lossProbability.setText(str(round(100-results["Calculated loss probability"]*100, 2)) + " %" if results["Calculated loss probability"] else "None")

            self._view_system = self._system

            print(pd.Series(data=results))
            self.timer.stop()
    
    def simulate_multiple(self, num_qubits, perturb, cross_check_fraction, losses, eavesdrop, add_uncertainty):
        for x_param_value in self.msd.x_param_values:
            if self.msd.x_param_name != "Cross check fraction":
                self._system.set_parameter(self.msd.x_param_name, x_param_value)
            else:
                cross_check_fraction = x_param_value/100

            result = self._system.simulate(
                n_bits=num_qubits, 
                losses=losses, 
                perturb=perturb, 
                cross_check_fraction=cross_check_fraction, 
                eavesdrop=eavesdrop, 
                add_uncertainty=add_uncertainty
            )

            if result is None:
                print("Aborted")
                return

            self.msd.used_x_param_values.append(x_param_value)

            self.msd.results.append(result)

            if self.msd.y_param_name == "QBER":
                self.msd.y_param_values.append(result[self.msd.y_param_name]*100)
            else:
                self.msd.y_param_values.append(result[self.msd.y_param_name])
            
            print(pd.Series(data=result))

            if self.msd.x_param_start == self.msd.x_param_end:
                plt.scatter([i+1 for i in range(len(self.msd.y_param_values))], self.msd.y_param_values, color=(0, 170/255, 127/255), s=12)
                plt.xlabel("Simulation number")
            else:
                plt.plot(self.msd.used_x_param_values, self.msd.y_param_values, "--", color=(0, 170/255, 127/255))
                plt.scatter(self.msd.used_x_param_values, self.msd.y_param_values, color=(0, 170/255, 127/255), s=12)
                plt.xlabel(self.msd.x_param_name + self.msd.x_suffix)

            plt.ylabel(self.msd.y_param_name + self.msd.y_suffix)
            plt.savefig("resources/multi_sim_plot.png")

            self.msd.pixmap = QtGui.QPixmap("resources/multi_sim_plot.png")

            self.msd.updated = True
        
        print(self.msd.used_x_param_values)
        print(self.msd.y_param_values)
    
    def multi_sim_progress_check_callback(self):
        if not self.msd.updated:
            return

        self._ui.multiPlot.setPixmap(self.msd.pixmap)
        self._ui.multiPlot.repaint()

        self._ui.multiProgressBar.setValue(round(100*len(self.msd.used_x_param_values)/len(self.msd.x_param_values)))

        if len(self.msd.used_x_param_values) == len(self.msd.x_param_values):
            if self.msd.x_param_start == self.msd.x_param_end:
                plt.scatter([i+1 for i in range(len(self.msd.y_param_values))], self.msd.y_param_values, color=(0, 170/255, 127/255), s=12)
                plt.xlabel("Simulation number")
                plt.ylabel(self.msd.y_param_name + self.msd.y_suffix)

                mean = round(np.mean(self.msd.y_param_values), 2)
                std = round(np.std(self.msd.y_param_values), 2)

                plt.axhline(y = mean, color = 'green', linestyle = '--', label="Mean: " + str(mean) + ", std: " + str(std))
                plt.legend()

                plt.savefig("resources/multi_sim_plot.png")
                pixmap = QtGui.QPixmap("resources/multi_sim_plot.png")
                self._ui.multiPlot.setPixmap(pixmap)
                self._ui.multiPlot.repaint()
        
                print("Mean", np.mean(self.msd.y_param_values))
                print("Std", np.std(self.msd.y_param_values))

            plt.close()
            self.timer.stop()

            print(self.msd.x_param_name, self.msd.used_x_param_values)
            print(self.msd.y_param_name, self.msd.y_param_values)
        
        self.msd.updated = False
    
    def run_multiple_simulations(self):
        perturb = self._ui.perturbationsEnabled.isChecked()
        losses = self._ui.lossesEnabled.isChecked()
        cross_check_fraction = self._ui.crossCheckFraction.value()/100
        num_qubits = self._ui.numberOfQubits.value()
        eavesdrop = self._ui.eavesdroppingEnabled.isChecked()
        add_uncertainty = self._ui.generationUncertaintyEnabled.isChecked()

        x_param_name = self._ui.xParameter.currentText()
        y_param_name = self._ui.yParameter.currentText()

        x_param_start = self._ui.startValue.value()
        x_param_end = self._ui.endValue.value()
        x_param_n_points = self._ui.numberOfPoints.value()

        self._ui.multiProgressBar.setValue(0)

        x_param_values = np.linspace(x_param_start, x_param_end, x_param_n_points)
        used_x_param_values = []

        y_param_values = []
        results = []

        plt.style.use("ggplot")

        if y_param_name == "S":
            plt.axhline(y = 2, color = 'gray', linestyle = '--')
        
        x_suffix = ""
        y_suffix = ""

        if x_param_name == "Fiber length":
            x_suffix = " [km]"
        elif x_param_name == "Fiber loss":
            x_suffix = " [dB/km]"
        elif x_param_name == "Perturb probability":
                x_suffix = " [%]"
        elif x_param_name == "SOP mean deviation":
                x_suffix = " [rad]"
        elif x_param_name == "Cross check fraction":
                x_suffix = " [%]"
        elif x_param_name == "Source generation rate":
                x_suffix = " [MHz]"
        elif x_param_name == "Detector efficiency":
                x_suffix = " [%]"
        elif x_param_name == "Source efficiency":
                x_suffix = " [%]"
            
        if y_param_name == "Key rate":
            y_suffix = " [Hz]"
        elif y_param_name == "QBER":
            y_suffix = " [%]"
        
        self.msd = MultisimData(
            x_param_name, 
            x_param_values, 
            y_param_name, 
            y_param_values, 
            results,
            x_param_start,
            x_param_end,
            x_suffix,
            y_suffix
        )

        self.run_thread = Thread(target = self.simulate_multiple, args = (num_qubits, perturb, cross_check_fraction, losses, eavesdrop, add_uncertainty))
        self.run_thread.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.multi_sim_progress_check_callback)
        self.timer.start(1000)


class MultisimData:
        def __init__(self, x_param_name, x_param_values, y_param_name, y_param_values, results, x_param_start, x_param_end, x_suffix, y_suffix):
            self.x_param_name = x_param_name
            self.x_param_values = x_param_values
            self.y_param_name = y_param_name
            self.y_param_values = y_param_values
            self.used_x_param_values = []
            self.results = results
            self.x_param_start = x_param_start
            self.x_param_end = x_param_end
            self.x_suffix = x_suffix
            self.y_suffix = y_suffix
            self.updated = False
            self.pixmap = None


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    style = QtWidgets.QStyleFactory.create("Fusion")
    app.setStyle(style)
    Window = QtWidgets.QMainWindow()
    ui = Ui_Window()
    ui.setupUi(Window)

    main = Main(ui)

    Window.show()
    sys.exit(app.exec_())