Clone repo and start program by running src/master.py from home directory containing src folder. Info on how the program works can be found in thesis.pdf.

May be convenient to create new Python virtual machine to install the necessary packages + run the program
- $ python -m venv /path/to/new/virtual/environment
- $ source /path/to/new/virtual/environment # launch vm
- $ deactivate /path/to/new/virtual/environment # terminate vm instance

Required libraries to be installed seperately. If using a Python vm, these should be installed after launching with "source" command.
- PyQt5: pip3 install pyqt5
- Qiskit: pip3 install qiskit==0.41.0
- Numpy: pip3 install numpy
- Matplotlib: pip3 install matplotlib
