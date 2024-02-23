import random
import matplotlib.pyplot as plt
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fault Coverage")
    parser.add_argument('--plot_cov', action='store_true', help="Plot fault coverage")
    parser.add_argument('--auto', action='store_true', help="Retain original function behavior")
    parser.add_argument('--filename', type=str, help="Filename for Read_netlist function")
    parser.add_argument('--test_vec', type=str, help="Test vector for simulation")
    args = parser.parse_args()

class Gate:
    def __init__(self, name, inputs, output):
        self.name = name
        self.inputs = inputs
        self.output = output

"""
Parses the netlist file to extract gate, input, and
output information by scanning each line, categorizing gate types, inputs,
and outputs.
"""
def Read_netlist(file_name):
    gates = []
    inputs = []
    outputs = []
    gate_inputs_dict = {}  # Dictionary to store unique gate inputs

    with open(file_name, 'r') as file:
        lines = file.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) > 0:
            #print(parts[0])
            gate_name = parts[0]

        if gate_name == 'INPUT':
            input_nets = [int(x) for x in parts[1:-1]]
            inputs = input_nets  # Store inputs as a list
            #print(inputs)
            for net in input_nets:
                gate_inputs_dict[net] = -1  # Assign input nets to -1
        elif gate_name == 'OUTPUT':
            output_nets = [int(x) for x in parts[1:-1]]
            outputs.extend(output_nets)  # Store outputs as a list
            #print(outputs)
        else:
            gate_inputs = [int(x) for x in parts[1:-1]]
            gate_output = int(parts[-1])
            gate = Gate(gate_name, gate_inputs, gate_output)
            #print(gate_name, gate_inputs, gate_output)
            gates.append(gate)
            for net in gate_inputs:
                gate_inputs_dict[net] = -1  # Assign gate inputs to -1

    # Convert the gate_inputs_dict keys to a list, removing repeated nets
    unique_gate_inputs = list(gate_inputs_dict.keys())
    #print(unique_gate_inputs)
    return gates, inputs, outputs, unique_gate_inputs

def logic_gates(gate, gate_inputs):
    input_values = gate_inputs
    if gate.name == 'AND':
        result = int(all(input_values))
    if gate.name == 'OR':
        result = int(any(input_values))
    if gate.name == 'NAND':
        result = int(not all(input_values))
    if gate.name == 'NOR':
        result = int(not any(input_values))
    if gate.name == 'INV':
        result = int(not input_values[0])
    if gate.name == 'BUF':
        result = input_values[0]
    return result

def initialize_nets(inputs, test_vector):
    nets = {}
    for i, net in enumerate(inputs):
        nets[net] = int(test_vector[i])
    return nets

"""
For Deductive Fault Simulation (START)
"""
def initialize_PIfault_lists(inputs, test_vector, auto=True):
    fault_list = {}
    for i, net in enumerate(inputs):
        fault_value = int(not int(test_vector[i]))
        if fault_value == 0:  # s-a-0 fault
            fault_list[net] = 0
        elif fault_value == 1:  # s-a-1 fault
            fault_list[net] = 1
        else:
            fault_list[net] = None
            """
    else:
        # Read fault values from s27_fault.txt and assign to fault_list
        with open('s27_fault.txt', 'r') as fault_file:
            lines = fault_file.readlines()
            for line in lines:
                net, value = line.strip().split()
                fault_list[int(net)] = int(value)
"""
    #print("INIT Fault Lists", fault_list)
    return fault_list


def deductive_fault_prop(gate, input_values, fault_list):
    #print("Actual",input_values)
    if gate.name == 'AND':
        result = int(all(input_values))
        faulty_ip1_result = int((int(not input_values[0])) & (int(input_values[1])))
        faulty_ip2_result = int((int(not input_values[1])) & (int(input_values[0])))
        #print("Faulty",(int(not input_values[0])), (int(input_values[1])), faulty_ip1_result)
        fault_list = list_propagation(result, faulty_ip1_result,faulty_ip2_result,gate,fault_list)

    if gate.name == 'OR':
        result = int(any(input_values))
        faulty_ip1_result = int((int(not input_values[0])) | (int(input_values[1])))
        faulty_ip2_result = int((int(not input_values[1])) | (int(input_values[0])))
        fault_list = list_propagation(result, faulty_ip1_result,faulty_ip2_result,gate,fault_list)

    if gate.name == 'NAND':
        result = int(not all(input_values))
        faulty_ip1_result = int(not ((int(not input_values[0])) & (int(input_values[1]))))
        faulty_ip2_result = int(not ((int(not input_values[1])) & (int(input_values[0]))))
        fault_list = list_propagation(result, faulty_ip1_result,faulty_ip2_result,gate,fault_list)

    if gate.name == 'NOR':
        result = int(not any(input_values))
        faulty_ip1_result = int(not ((int(not input_values[0])) | (int(input_values[1]))))
        faulty_ip2_result = int(not ((int(not input_values[1])) | (int(input_values[0]))))
        fault_list = list_propagation(result, faulty_ip1_result,faulty_ip2_result,gate,fault_list)

    if gate.name == 'INV':
        result = int(not input_values[0])
        faulty_ip1_result = int(input_values[0])
        faulty_ip2_result = int(input_values[0])
        fault_list = list_propagation(result, faulty_ip1_result, faulty_ip2_result, gate, fault_list)

    if gate.name == 'BUF':
        result = input_values[0]
        faulty_ip1_result = int(not input_values[0])
        faulty_ip2_result = int(not input_values[0])
        fault_list = list_propagation(result, faulty_ip1_result, faulty_ip2_result, gate, fault_list)
    return fault_list

def list_propagation(result, faulty_ip1_result, faulty_ip2_result, gate, fault_list):
    gate_output_faults = {}  # Initialize an empty dictionary

    if result != faulty_ip1_result and result != faulty_ip2_result:
        #print("Not Equal")
        gate_output_faults[gate.output] = {i: fault_list[i] for i in gate.inputs}

    if result == faulty_ip1_result and result == faulty_ip2_result:
        #print("Equal")
        if gate.output not in gate_output_faults:
            gate_output_faults[gate.output] = {}  # Initialize if it doesn't exist

    if result == faulty_ip1_result and result != faulty_ip2_result:
        #print("2 props")
        gate_output_faults[gate.output] = {gate.inputs[1]: fault_list[gate.inputs[1]]}

    if result != faulty_ip1_result and result == faulty_ip2_result:
        #print("1 props")
        gate_output_faults[gate.output] = {gate.inputs[0]: fault_list[gate.inputs[0]]}

    if gate.output in gate_output_faults:
        gate_output_faults[gate.output][gate.output] = int(not result)
    else:
        gate_output_faults[gate.output] = {gate.output: int(not result)}

    fault_list.update(gate_output_faults)
    #print("CUpdated Fault Lists", fault_list)
    return fault_list

"""
For Deductive Fault Simulation (END)
"""

def simulate_logic(gates, nets,fault_list):
    stack = []
    processed_gates = set()  # Set to keep track of processed gates

    for gate in gates:
        all_inputs_assigned = all(nets[net] != -1 for net in gate.inputs)
        if all_inputs_assigned:
            stack.append(gate)
            processed_gates.add(gate)  # Add the gate to processed gates
            #print(gate.name, gate.inputs)

    while stack:
        gate = stack.pop()
        input_values = [nets[net] for net in gate.inputs]
        result = logic_gates(gate, input_values)
        nets[gate.output] = result
        deductive_fault_prop(gate,input_values, fault_list)
        #print(gate.name, input_values, gate.inputs, gate.output, result)
        #print(nets)

        # Check all gates again for input assignment, excluding processed gates
        for next_gate in gates:
            if next_gate not in processed_gates and all(nets[net] != -1 for net in next_gate.inputs):
                #print(next_gate.name, next_gate.inputs)
                stack.append(next_gate)
                processed_gates.add(next_gate)  # Add the gate to processed gates
    #print("#of Gates",len(processed_gates))
    return nets

def count_nested_faults(fault_dict):
    fault_count = 0
    for value in fault_dict.values():
        if isinstance(value, dict):
            fault_count += count_nested_faults(value)
        elif value is not None:
            fault_count += 1
    return fault_count

def save_output_net_faults(fault_list, output_nets, file_name):
    printed_faults = set()  # Keep track of printed faults
    with open(file_name, 'w') as file:
        for net in sorted(output_nets):
            if isinstance(fault_list.get(net), dict):
                printed_faults.update(print_nested_faults(fault_list[net], file, net, printed_faults))
            else:
                printed_fault = (net, fault_list[net])
                if printed_fault not in printed_faults:
                    file.write(f"{net} stuck at {fault_list[net]}\n")
                    printed_faults.add(printed_fault)

def print_nested_faults(fault_dict, file, net, printed_faults):
    printed_faults_nested = set()  # Keep track of printed faults within nested levels
    for net, value in sorted(fault_dict.items()):
        if isinstance(value, dict):
            printed_faults_nested.update(print_nested_faults(value, file, net, printed_faults))
        else:
            printed_fault = (net, value)
            if printed_fault not in printed_faults and printed_fault not in printed_faults_nested:
                file.write(f"{net} stuck at {value}\n")
                printed_faults.add(printed_fault)  # Update the printed_faults set with the new unique fault
                printed_faults_nested.add(printed_fault)
    return printed_faults_nested

# Function to parse the lines in output_net_faults.txt
def parse_output_net_faults(file_name):
    def extract_number(fault_str):
        # Extract the first number from the fault string and convert it to an integer
        return int(fault_str.split()[0])

    with open(file_name, 'r') as file:
        parsed_faults = [line.strip() for line in file if line.strip()]

    # Sort the parsed faults based on the extracted numbers
    parsed_faults.sort(key=extract_number)
    #print(parsed_faults)
    return parsed_faults


# Function to create a new output file with sorted and unique parsed faults
def create_sorted_output_file(parsed_faults, new_file_name):
    with open(new_file_name, 'w') as file:
        for parsed_fault in parsed_faults:
            file.write(parsed_fault + '\n')  # Write each sorted fault to the new file


# Function to count the number of keys in the nets dictionary
def count_nets(nets):
    return sum(1 for value in nets.values() if value != -1)

# Function to generate a random test vector
def generate_random_test_vector(inputs):
    return ''.join(random.choice('01') for _ in range(len(inputs)))


# Function to calculate fault coverage
def calculate_fault_coverage(gates, inputs, outputs, unique_gate_inputs, num_tests):
    total_unique_faults = set()  # Initialize the set for unique faults across all tests

    for _ in range(num_tests):
        test_vector = generate_random_test_vector(inputs)
        # print(test_vector)
        nets = {net: -1 for net in unique_gate_inputs + outputs}
        nets.update(initialize_nets(inputs, test_vector))
        fault_list = initialize_PIfault_lists(inputs, test_vector, args.auto)
        nets = simulate_logic(gates, nets, fault_list)

        # Save output net faults to a file
        save_output_net_faults(fault_list, outputs, "output_net_faults.txt")
        parsed_faults = parse_output_net_faults("output_net_faults.txt")

        unique_faults = set(parsed_faults)  # Create a set of unique faults for the current test
        total_unique_faults.update(unique_faults)  # Add unique faults to the set of all unique faults

        print(test_vector, len(unique_faults), len(total_unique_faults))

    total_fault_count = len(total_unique_faults)  # Calculate the total unique fault count
    print(f"Number of Unique Faults: {total_fault_count}")
    print(f"Number of Faults: {2 * count_nets(nets)}")
    fault_coverage = (total_fault_count / (2 * count_nets(nets)))  # Use accumulated unique fault count

    return fault_coverage

# PODEM Simulation Purpose :: Test vectors
test_vectors = [args.test_vec]
gates, inputs, outputs, unique_gate_inputs = Read_netlist(args.filename)

# Deductive Fault Simulation Purpose :: Test vectors
"""
test_vectors = ['0000011']#['1101101', '0101001']
#gates, inputs, outputs, unique_gate_inputs = Read_netlist("s27.txt")
"""

"""
test_vectors = ['10101010101010101']#['10101011110010101', '11101110101110111']
gates, inputs, outputs, unique_gate_inputs = Read_netlist("s298f_2.txt")
"""

"""
test_vectors = ['111010111010101010001100']# ['101010101010111101111111', '111010111010101010001100']
gates, inputs, outputs, unique_gate_inputs = Read_netlist("s344f_2.txt")
"""

"""
test_vectors = ['111111101010101010001111']#['101000000010101011111111', '111111101010101010001111']
gates, inputs, outputs, unique_gate_inputs = Read_netlist("s349f_2.txt")
"""

"""
test_vectors = ['1110'] #, '1001','1100', '0100']
gates, inputs, outputs, unique_gate_inputs = Read_netlist("test_file.txt")
"""

# Generate random test vectors for fault coverage analysis
# Initialize empty lists to store the results
if args.plot_cov:
    num_tests_list = list(range(1, 40))
    fault_coverage_list = []

    # Calculate fault coverage for different numbers of tests
    for num_tests in num_tests_list:
        fault_coverage = calculate_fault_coverage(gates, inputs, outputs, unique_gate_inputs, num_tests)
        fault_coverage_list.append(fault_coverage)

    # Plot the results
    plt.figure()
    plt.plot(num_tests_list, [cov * 100 for cov in fault_coverage_list], marker='o')
    plt.xlabel('Number of Tests')
    plt.ylabel('Fault Coverage (%)')
    plt.title('Fault Coverage vs. Number of Tests')
    plt.grid(True)
    plt.show()


# Simulate for each test vector
for test_vector in test_vectors:
    # Initialize nets with inputs and outputs but set input values based on the test vector
    nets = {net: -1 for net in unique_gate_inputs + outputs}
    #print(f"1Current nets: {nets}")
    nets.update(initialize_nets(inputs, test_vector))  # Update input values based on the test vector
    fault_list = initialize_PIfault_lists(inputs, test_vector, args.auto)
    #print(f"Current nets: {nets}")
    nets = simulate_logic(gates,nets,fault_list)
    output_values = [nets[net] for net in outputs]
    #print(outputs)
    # Save output net faults to a file
    save_output_net_faults(fault_list, outputs, "output_net_faults.txt")
    parsed_faults = parse_output_net_faults("output_net_faults.txt")
    create_sorted_output_file(parsed_faults, "sorted_output_net_faults.txt")
    print(f"Test Vector: {test_vector}, Output Values: {output_values}")


