"""
File containing Logic Gate Operations
"""
def not_gate(inp1):
    if inp1 == 1:
        gate_output = 0
    if inp1 == 0:
        gate_output = 1
    if inp1 == 'D':
        gate_output = 'Dbar'
    if inp1 == 'Dbar':
        gate_output = 'D'
    if inp1 == 'x':
        gate_output = 'x'
    return gate_output

def buf_gate(inp1):
    gate_output = inp1
    return gate_output

def and_gate(inp1, inp2):
    if inp1 == 0 or inp2 == 0:
        gate_output = 0
    if inp1 == 1:
        gate_output = inp2
    if inp2 == 1:
        gate_output = inp1
    if inp1 == 'D':
        if inp2 == 'D':
            gate_output = 'D'
        if inp2 == 'Dbar':
            gate_output = 0
        if inp2 == 'x':
            gate_output = 'x'
    if inp1 == 'Dbar':
        if inp2 == 'D':
            gate_output = 0
        if inp2 == 'Dbar':
            gate_output = 'Dbar'
        if inp2 == 'x':
            gate_output = 'x'
    if inp1 == 'x':
        if inp2 == 'D' or inp2 == 'Dbar' or inp2 == 'x':
            gate_output = 'x'
    return gate_output

def or_gate(inp1, inp2):
    if inp1 == 1 or inp2 == 1:
        gate_output = 1
    if inp1 == 0:
        gate_output = inp2
    if inp2 == 0:
        gate_output = inp1
    if inp1 == 'D':
        if inp2 == 'D':
            gate_output = 'D'
        if inp2 == 'Dbar':
            gate_output = 1
        if inp2 == 'x':
            gate_output = 'x'
    if inp1 == 'Dbar':
        if inp2 == 'D':
            gate_output = 1
        if inp2 == 'Dbar':
            gate_output = 'Dbar'
        if inp2 == 'x':
            gate_output = 'x'
    if inp1 == 'x':
        if inp2 == 'D' or inp2 == 'Dbar' or inp2 == 'x':
            gate_output = 'x'
    return gate_output

def nor_gate(inp1, inp2):
    or_output = or_gate(inp1, inp2)
    gate_output = not_gate(or_output)
    return gate_output

def nand_gate(inp1, inp2):
    and_output = and_gate(inp1, inp2)
    gate_output = not_gate(and_output)
    return gate_output

def xor_gate(inp1, inp2):
    if inp1 == inp2:
        gate_output = 0
    if inp1 != inp2:
        gate_output = 1
    return gate_output