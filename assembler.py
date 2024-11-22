import argparse
import struct
import xml.etree.ElementTree as ET

def assemble_instruction(line):
    fields = line.split()
    command = int(fields[0])
    b = int(fields[1])
    c = int(fields[2])
    d = int(fields[3]) if len(fields) > 3 else 0

    # Упаковка команды в 14 байт
    if command == 90:  # Загрузка константы
        return struct.pack('<B Q Q', command, b, c)
     #то команда, а два следующих значения (Q) — это два операнда в формате "беззнаковое 8-байтовое целое").
    elif command == 1:  # Чтение значения из памяти
        return struct.pack('<B Q Q B', command, b, c, d) #упаковывается в 17 байт (<B Q Q B — это означает команду и три операнда).
    elif command == 62:  # Запись значения в память
        return struct.pack('<B Q Q', command, b, c)
    elif command == 137:  # Унарная операция sqrt()
        return struct.pack('<B Q B Q', command, b, c, d)
    else:
        raise ValueError(f"Unknown command: {command}")

def assemble(input_path, output_path, log_path):
    binary_data = bytearray()
    root = ET.Element("log")

    with open(input_path, 'r') as input_file:
        for line in input_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # Пропуск комментариев и пустых строк

            instruction = assemble_instruction(line)
            binary_data.extend(instruction)
            
            instr_elem = ET.SubElement(root, "log")
            ET.SubElement(instr_elem, "instruction").text = line
            ET.SubElement(instr_elem, "binary").text = instruction.hex()

    with open(output_path, 'wb') as output_file:
        output_file.write(binary_data)

    
    tree = ET.ElementTree(root)
    ET.indent(root)
    tree.write(log_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assembler for UVM")
    parser.add_argument("--input", required=True, help="Path to the input assembly file")
    parser.add_argument("--output", required=True, help="Path to the output binary file")
    parser.add_argument("--log", required=True, help="Path to the log file")
    args = parser.parse_args()

    assemble(args.input, args.output, args.log)

