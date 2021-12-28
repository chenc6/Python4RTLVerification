import cocotb
from pyuvm import *
import random
import statistics
# Mailbox example


# # Analysis ports
# ## The uvm_analysis_port
class NumberGenerator(uvm_component):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        self.raise_objection()
        for _ in range(9):
            nn = random.randint(1, 10)
            print(nn, end=" ")
            self.ap.write(nn)
        print("")
        self.drop_objection()


# ## Extending the uvm_analysis_export class
class Adder(uvm_analysis_export):
    def start_of_simulation_phase(self):
        self.sum = 0

    def write(self, nn):
        self.sum += nn

    def report_phase(self):
        self.logger.info(f"Sum: {self.sum}")


class AdderTest(uvm_test):
    def build_phase(self):
        self.num_gen = NumberGenerator("num_gen", self)
        self.sum = Adder("sum", self)

    def connect_phase(self):
        self.num_gen.ap.connect(self.sum)


@cocotb.test()
async def add_test(_):
    """Testing the adder export"""
    await uvm_root().run_test("AdderTest")


# ## Instantiate a uvm_tlm_analysis_fifo
class Average(uvm_component):
    def build_phase(self):
        self.fifo = uvm_tlm_analysis_fifo("fifo", self)
        self.nbgp = uvm_nonblocking_get_port("nbgp", self)

    def connect_phase(self):
        self.nbgp.connect(self.fifo.get_export)

    def report_phase(self):
        success = True
        sum = 0
        count = 0
        while success:
            success, nn = self.nbgp.try_get()
            if success:
                sum += nn
                count += 1
        self.logger.info(f"Average: {sum/count:0.2f}")


class AverageTest(uvm_test):
    def build_phase(self):
        self.num_gen = NumberGenerator("num_gen", self)
        self.sum = Adder("sum", self)
        self.avg = Average("avg", self)

    def connect_phase(self):
        self.num_gen.ap.connect(self.sum)
        self.num_gen.ap.connect(self.avg.fifo.analysis_export)


@cocotb.test()
async def avg_test(_):
    """Test the Average"""
    await uvm_root().run_test("AverageTest")


# ## Extend the uvm_subscriber class
class Median(uvm_subscriber):

    def start_of_simulation_phase(self):
        self.numb_list = []

    def write(self, nn):
        self.numb_list.append(nn)

    def report_phase(self):
        self.logger.info(f"Median: {statistics.median(self.numb_list)}")


class MedianTest(uvm_test):
    def build_phase(self):
        self.num_gen = NumberGenerator("num_gen", self)
        self.sum = Adder("sum", self)
        self.avg = Average("avg", self)
        self.median = Median("median", self)

    def connect_phase(self):
        self.num_gen.ap.connect(self.sum)
        self.num_gen.ap.connect(self.avg.fifo.analysis_export)
        self.num_gen.ap.connect(self.median.analysis_export)


@cocotb.test()
async def median_test(_):
    """Test the Median"""
    await uvm_root().run_test("MedianTest")
