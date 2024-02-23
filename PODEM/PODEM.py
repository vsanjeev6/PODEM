import sys
import re
import PODEM_Logic_Gates as pdm_lg

class Gate:
    def __init__(self, name, inputs, output):
        self.name = name
        self.inputs = inputs
        self.output = output

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
            #print("RN",inputs)
            for net in input_nets:
                gate_inputs_dict[net] = -1  # Assign input nets to -1
        elif gate_name == 'OUTPUT':
            output_nets = [int(x) for x in parts[1:-1]]
            outputs.extend(output_nets)  # Store outputs as a list
            #print("RN",outputs)
        else:
            gate_inputs = [int(x) for x in parts[1:-1]]
            gate_output = int(parts[-1])
            gate = Gate(gate_name, gate_inputs, gate_output)
            #print("RN", gate_name, gate_inputs, gate_output)
            gates.append(gate)
            for net in gate_inputs:
                gate_inputs_dict[net] = -1  # Assign gate inputs to -1

    # Convert the gate_inputs_dict keys to a list, removing repeated nets
    unique_gate_inputs = list(gate_inputs_dict.keys())
    #print("RN", unique_gate_inputs)
    return gates, inputs, outputs, unique_gate_inputs

"""
Output : [list of a gate's inputs and output][all gate outputs]
"""
def create_gate_list(gate_type):
    f.seek(0)
    gate_list = []
    gate_out = []
    gate_count = 0

    for line in f:
        if line.startswith(gate_type):
            gate_number = line.partition(' ')[2]  # separate char from num
            gate_num1 = gate_number.rstrip('\n')  # remove \n
            gate_list.append(gate_num1.split(" "))
            gate_num1 = list(gate_num1.split(" "))
            if gate_type == 'INV' or gate_type == 'BUF':
                gate_out.append(gate_num1[1])
            else:
                gate_out.append(gate_num1[2])
            gate_list[gate_count] = list(map(int, gate_list[gate_count]))
            gate_count += 1
            #print("CGL",gate_list, gate_out)
    return [gate_list, gate_out]

"""
Parsing the Fault-lists file (_fault.txt)
"""
def create_fault_list(fault_list):
    fault_list_ip = []
    with open(sys.argv[2], 'r') as f:
        for line in f:
            fault_list_ip.append(re.findall(r'\d{1,3}', line))

        for i in range(len(fault_list_ip)):
            fault_list.append(fault_list_ip[i])
    print("Fault", fault_list)
    return fault_list

"""
Find which gate has the target pin as the output
"""
def find_gate(pin):
    pin = str(pin)
    gate_types = {
        'and': (and_out, and_list, 'and', 0, 0),
        'or': (or_out, or_list, 'or', 0, 1),
        'nand': (nand_out, nand_list, 'nand', 1, 0),
        'nor': (nor_out, nor_list, 'nor', 1, 1),
        'inv': (inv_out, inv_list, 'inv', 1, None),
        'buf': (buf_out, buf_list, 'buf', 0, None)
    }

    for gate_type, (out_list, gate_list, gate_str, inv_par, ctr_val) in gate_types.items():
        if out_list.__contains__(pin):
            gate = []
            pin_index = out_list.index(pin)
            pin_gate = gate_list[pin_index]
            gate.append(pin_gate)
            gate.append(gate_str)
            gate.append(inv_par)
            gate.append(ctr_val)
            return gate
    return [[int(pin)], 'PI', 0]

"""
D-Frontier Function : Gates whose output value is x, while one or more Inputs are D or Dbar
"""
def create_D_front():
    d_list = []
    for df in range(len(Tot_pins)):
        pin_no = df
        gate = find_gate(pin_no + 1)
        #print("D_FRONT", gate)
        gate_list = gate[0]

        if gate[1] in ['and', 'nand', 'or', 'nor']:
            # Check if either of the 2 inputs in the above gates are D or Dbar
            if Tot_pins[gate_list[2] - 1] == 'x' and (Tot_pins[gate_list[0] - 1] in ['D', 'Dbar']):
                d_list.append(pin_no + 1)
            if Tot_pins[gate_list[2] - 1] == 'x' and (Tot_pins[gate_list[1] - 1] in ['D', 'Dbar']):
                d_list.append(pin_no + 1)
    #print("D_lists",d_list)
    return d_list

"""
Objective Function of PODEM
"""
def objective(target_pin,stuck_at):
    if Tot_pins[target_pin-1] == 'x':
        return target_pin, pdm_lg.not_gate(stuck_at)

    if not len(d_list) == 0:
        gate_pin = d_list[len(d_list)-1]
        d_list.pop()
        gate = find_gate(gate_pin)
        gate_list = gate[0]

        if Tot_pins[gate_list[0]-1] == 'x':
            ctr_val = gate[3]
            ctr_val = pdm_lg.not_gate(ctr_val)
            return gate_list[0],ctr_val
        if Tot_pins[gate_list[1]-1] == 'x':
            ctr_val = gate[3]
            ctr_val = pdm_lg.not_gate(ctr_val)
            return gate_list[1],ctr_val
    return 'no d list',1

"""
Backtrace functions
"""
def backtrace(target_pin,pin_val):
    global bt_loop
    bt_loop = 0
    pin_no = mod_backtrace(target_pin)

    if pin_no == 'no x path':
        return 'no pin value','no pin value'

    # Find Inversion parity of the path
    if gate_inv.count(1) % 2 == 0:
        # Even => Assign same value as objective
        inv_par = 0
    else:
        # Odd => Assign opposite value as objective
        inv_par = 1
    pin_val_new = pdm_lg.xor_gate(pin_val,inv_par)
    return pin_no,pin_val_new

def mod_backtrace(pin_no):
    x_list = []
    global bt_loop

    if pin_no == 'no d list':
        return 'no x path'

    gate = find_gate(pin_no)
    gate_list = gate[0]
    gate_inv.append(gate[2])
    #print("BT GATE:", gate, gate_list, gate_inv)

    bt_loop += 1
    if bt_loop >= size:
        return 'no x path'

    if gate[1] == 'and' or gate[1] == 'nand' or gate[1] == 'or' or gate[1] == 'nor':
        if PI_BL.__contains__(gate_list[0]) and PI_BL.__contains__(gate_list[1]):
            if len(x_list) == 1 or len(x_list) == 0:
                return 'no x path'
            #print("XLIST1:", x_list)
            x_list.pop()
            if len(x_list[len(x_list)-1]) == 2 :
                gate_list[0] = x_list[len(x_list)-1][1]
                return mod_backtrace(gate_list[0])
            else:
                while not len(x_list[len(x_list)-1]) == 2:
                    if len(x_list) == 1:
                        break
                    x_list.pop()
                if len(x_list) == 1:
                    return 'no x path'
                gate_list[0] = x_list[len(x_list) - 1][1]
                return mod_backtrace(gate_list[0])
        if PI_BL.__contains__(gate_list[0]):
            gate_list[0] = gate_list[1]
            con = [gate_list[0]]
            x_list.append(con)
            #print("XLIST2:", x_list)
            return mod_backtrace(gate_list[0])
        # When only inp1 is x
        if Tot_pins[gate_list[0]-1] == 'x'and not input_list.__contains__(gate_list[0]) and not Tot_pins[gate_list[0]-1] == Tot_pins[gate_list[1]-1]:
            con = [gate_list[0]]
            x_list.append(con)
            #print("XLIST3:", x_list)
        # When only inp2 is x
        if not Tot_pins[gate_list[0]-1] == 'x' and Tot_pins[gate_list[1]-1] == 'x'and not input_list.__contains__(gate_list[1]) and not Tot_pins[gate_list[0]-1] == Tot_pins[gate_list[1]-1]:
            gate_list[0] = gate_list[1]
            con = [gate_list[0]]
            x_list.append(con)
            #print("XLIST4:", x_list)
            return mod_backtrace(gate_list[0])
        # When both gate inputs are x
        if Tot_pins[gate_list[1]-1] == 'x' and Tot_pins[gate_list[0]-1] == Tot_pins[gate_list[1]-1] and not gate_list[0] == gate_list[1]:
            con = [str(gate_list[0])]
            con.append(str(gate_list[1]))
            con = list(map(int, con))
            x_list.append(con)
            #print("XLIST5:", x_list)

        if Tot_pins[gate_list[1] - 1] == 'x' and Tot_pins[gate_list[0] - 1] == Tot_pins[gate_list[1] - 1] and gate_list[0] == gate_list[1]:
            con = [gate_list[0]]
            x_list.append(con)
            #print("XLIST6:", x_list)

        if input_list.__contains__(gate_list[0]) and Tot_pins[gate_list[0]-1] == 'x' and (not PI_BL.__contains__(gate_list[0])):
            PI_BL.append(gate_list[0])
            return gate_list[0]

        if Tot_pins[gate_list[0]-1] == 'x':
            return mod_backtrace(gate_list[0])

    if gate[1] == 'PI' and (not PI_BL.__contains__(gate_list[0])):
        PI_BL.append(gate_list[0])
        return gate_list[0]
    else:
        if PI_BL.__contains__(gate_list[0]):
            if len(x_list) == 1 or len(x_list) == 0:
                return 'no x path'

            x_list.pop()
            if len(x_list[len(x_list)-1]) == 2 :
                gate_list[0] = x_list[len(x_list)-1][1]
                return mod_backtrace(gate_list[0])
            else:
                while not len(x_list[len(x_list)-1]) == 2:
                    if len(x_list) == 1:
                        break
                    x_list.pop()
                if len(x_list) == 1:
                    return 'no x path'
                gate_list[0] = x_list[len(x_list) - 1][1]
                return mod_backtrace(gate_list[0])

        if Tot_pins[gate_list[0]-1] == 'x'and not input_list.__contains__(gate_list[0]):
            con = [gate_list[0]]
            x_list.append(con)

        if (input_list.__contains__(gate_list[0]) and Tot_pins[gate_list[0]-1] == 'x') and (not PI_BL.__contains__(gate_list[0])):
            PI_BL.append(gate_list[0])
            return gate_list[0]
        if Tot_pins[gate_list[0]-1] == 'x':
            return mod_backtrace(gate_list[0])
    return 'no x path'

"""
Forward Implication
"""
def eval_logic():
    if input_list.__contains__(target_pin):
        if Tot_pins[target_pin - 1] == 0 and val_stuck_at == 1:
            Tot_pins[target_pin - 1] = 'Dbar'
        if Tot_pins[target_pin - 1] == 1 and val_stuck_at == 0:
            Tot_pins[target_pin - 1] = 'D'

    gates = [and_list, or_list, nor_list, nand_list]
    functions = [pdm_lg.and_gate, pdm_lg.or_gate, pdm_lg.nor_gate, pdm_lg.nand_gate]

    for loop in range(20):
        for gate_list, function in zip(gates, functions):
            for i in range(len(gate_list)):
                gate_opr = function(Tot_pins[gate_list[i][0] - 1], Tot_pins[gate_list[i][1] - 1])
                Tot_pins[gate_list[i][2] - 1] = gate_opr

                if gate_list[i][2] == target_pin:
                    if Tot_pins[gate_list[i][2] - 1] == 0 and val_stuck_at == 1:
                        Tot_pins[gate_list[i][2] - 1] = 'Dbar'
                    elif Tot_pins[gate_list[i][2] - 1] == 1 and val_stuck_at == 0:
                        Tot_pins[gate_list[i][2] - 1] = 'D'

        for gate_list in [inv_list, buf_list]:
            for i in range(len(gate_list)):
                if gate_list == inv_list:
                    gate_opr = pdm_lg.not_gate(Tot_pins[gate_list[i][0] - 1])
                else:
                    gate_opr = Tot_pins[gate_list[i][0] - 1]

                Tot_pins[gate_list[i][1] - 1] = gate_opr
        
                if gate_list[i][1] == target_pin:
                    if Tot_pins[gate_list[i][1] - 1] == 0 and val_stuck_at == 1:
                        Tot_pins[gate_list[i][1] - 1] = 'Dbar'
                    elif Tot_pins[gate_list[i][1] - 1] == 1 and val_stuck_at == 0:
                        Tot_pins[gate_list[i][1] - 1] = 'D'

    #print("Tot Pins", Tot_pins)
    return Tot_pins


def PODEM(target_pin1,stuck_at1):
    global d_list
    d_list = create_D_front()
    Tot_pins = eval_logic()

    for out_len in range(len(output_list)):
        if Tot_pins[output_list[out_len]-1] == 'D' or Tot_pins[output_list[out_len]-1] == 'Dbar':
            return 'Detected'

    req_pin,pin_val1 = objective(target_pin1,stuck_at1)
    pin_no,pin_val = backtrace(req_pin,pin_val1)
    if pin_no == 'no pin value': #no test possible
        return 'Undetected'

    Tot_pins[pin_no-1] = pin_val
    Tot_pins = eval_logic()
    d_list = create_D_front()

    if PODEM(target_pin1,stuck_at1) == 'Detected':
        return 'Detected'
    Tot_pins[pin_no - 1] = pdm_lg.not_gate(pin_val)
    Tot_pins = eval_logic()
    d_list = create_D_front()

    if PODEM(target_pin1,stuck_at1) == 'Detected':
        return 'Detected'
    Tot_pins[pin_no - 1] = 'x'
    Tot_pins = eval_logic()
    d_list = create_D_front()
    return 'Undetected'


def output_write(all_output):
    max_outputs = len(output_list)
    all_out = []
    for i in range(0, max_outputs):  # till all the inputs are inputted
        all_out.append((Tot_pins[output_list[i] - 1]))
    all_output.append(all_out)
    return all_output

def input_write(all_input):
    max_inputs = len(input_list)
    all_in_1 = []
    for i in range(0, max_inputs):  # till all the inputs are inputted
        if Tot_pins[input_list[i] - 1] == 'D':
            Tot_pins[input_list[i] - 1] = 1
        if Tot_pins[input_list[i] - 1] == 'Dbar':
            Tot_pins[input_list[i] - 1] = 0
        all_in_1.append((Tot_pins[input_list[i] - 1]))
    all_input.append(all_in_1)
    return all_input

fault_list = []
fault_list = create_fault_list(fault_list)
FF_Tot_pins = []
FF_all_output = []
FF_all_inp = []
PODEM_result = []
for faults in range(len(fault_list)):
    # Circuit File Open
    with open(sys.argv[1], 'r') as f:
        all_output = []
        all_input = []
        pin_list = []
        global target_pin,val_stuck_at,size
        target_pin = int(fault_list[faults][0])  # stuck at 1
        val_stuck_at = int(fault_list[faults][1])
        size = 0
        for line in f:
            size = size + 1
            Pins = re.findall(r'\d{1,3}', line)  # finds numbers in each line
            Pins = list(map(int, Pins))  # Converts strings to int
            if Pins:
                Pins = max(Pins)  # max in a line
                pin_list.append(Pins)  # make a list

        Num_pins = max(pin_list)  # max pin number
        Tot_pins = ['x'] * Num_pins

        gates, input_list, output_list, unique_gate_inputs = Read_netlist(sys.argv[1])
        # Access individual gate lists and outputs
        inv_list, inv_out = create_gate_list('INV')
        and_list, and_out = create_gate_list('AND')
        nand_list, nand_out = create_gate_list('NAND')
        or_list, or_out = create_gate_list('OR')
        nor_list, nor_out = create_gate_list('NOR')
        buf_list, buf_out = create_gate_list('BUF')
        xor_list, xor_out = create_gate_list('XOR')

    PI_BL = []
    gate_inv = []
    bt_loop = 0

    Tot_pins = eval_logic()

    # PODEM
    test_result = PODEM(target_pin,val_stuck_at)

    PODEM_result.append(test_result)
    all_output = output_write(all_output)
    # To retain the results after multiple loops
    FF_all_output.append(all_output[0])
    FF_Tot_pins.append(Tot_pins)
    all_input = input_write(all_input)
    FF_all_inp.append(all_input[0])

print('PODEM RESULT:',PODEM_result)
max_inputs = len(input_list)

"""
Used to store the test stimulus as generated by PODEM
"""
with open('Test_stimulus.txt', 'w') as f:
    for k in range(len(FF_all_inp)):
        for j in range(0, max_inputs):
            f.write(str(FF_all_inp[k][j]))
        f.write('\n')
        f.write(PODEM_result[k])
        f.write('\n')
"""
Used to store the test vectors to be used in Deductive Fault simulator
"""
with open('Test_Vectors_For_Ded_Fault_Sim.txt', 'w') as f:
    for k in range(len(FF_all_inp)):
        for j in range(0, max_inputs):
            if FF_all_inp[k][j] == 'x':
                f.write('0')
            if FF_all_inp[k][j] == 0 or FF_all_inp[k][j] == 1:
                f.write(str(FF_all_inp[k][j]))
        f.write('\n')