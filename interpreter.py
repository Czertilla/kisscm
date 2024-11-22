import struct
import xml.etree.ElementTree as ET


def assemble(input_path, output_binary, log_path):
    with open(input_path, 'r') as file:
        lines = file.readlines()

    binary_data = bytearray()
    root = ET.Element("log")

    commands = {
        "LOAD_CONST": 12,
        "READ": 10,
        "WRITE": 7,
        "MOD": 6,
    }

    for line in lines:
        parts = line.strip().split()
        cmd = parts[0]
        arg = int(parts[1]) if len(parts) > 1 else 0
        A = commands.get(cmd, 0)
        B = arg

        instruction = (A << 28) | (B & 0x0FFFFFFF)
        binary_data.extend(struct.pack(">I", instruction))  # Big-endian

        instr_elem = ET.SubElement(root, "instruction")
        ET.SubElement(instr_elem, "name").text = cmd
        ET.SubElement(instr_elem, "binary").text = f"0x{instruction:08X}"
        ET.SubElement(instr_elem, "A").text = str(A)
        ET.SubElement(instr_elem, "B").text = str(B)

    with open(output_binary, "wb") as bin_file:
        bin_file.write(binary_data)

    tree = ET.ElementTree(root)
    tree.write(log_path, encoding="utf-8", xml_declaration=True)


def interpret(binary_file, result_file, memory_range):
    memory = [0] * 1024
    accumulator = 0

    with open(binary_file, "rb") as file:
        binary_data = file.read()

    for i in range(0, len(binary_data), 4):
        instruction = struct.unpack(">I", binary_data[i:i+4])[0]
        A = (instruction >> 28) & 0xF
        B = instruction & 0x0FFFFFFF
        print(A)
        print(B)

        if A == 12:  # LOAD_CONST
            accumulator = B
        elif A == 10:  # READ
            accumulator = memory[accumulator]
        elif A == 7:  # WRITE
            memory[B] = accumulator
        elif A == 6:  # MOD
            print(memory[B])
            print(accumulator)
            accumulator %= memory[B]
            print(accumulator)

    root = ET.Element("result")
    for address in range(memory_range[0], memory_range[1]):
        value = memory[address]
        mem_elem = ET.SubElement(root, "memory")
        ET.SubElement(mem_elem, "address").text = str(address)
        ET.SubElement(mem_elem, "value").text = str(value)

    tree = ET.ElementTree(root)
    tree.write(result_file, encoding="utf-8", xml_declaration=True)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, help="Path to the binary file")
    parser.add_argument("--result", required=True, help="Path to the result file")
    parser.add_argument("--range", required=True, help="Memory range (start:end)")
    parser.add_argument("--log", required=True, help="Path to log file")

    args = parser.parse_args()
    memory_range = list(map(int, args.range.split(":")))

    
    assemble(parser.binary, parser.result, "log.xml")
    interpret(parser.result, "result.xml", memory_range)




