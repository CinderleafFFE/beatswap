import os.path as path
import argparse

inverse = {
    '1': '5',
    '2': '6',
    '3': '7',
    '4': '8',
    '5': '1',
    '6': '2',
    '7': '3',
    '8': '4'
}

def swap2367(filename: str):
    with open(filename, 'r') as f:
        notation = f.read()
    # Since time is separated with comma,
    # and simultaneous notes are separated with slash
    start_pos = 0
    end_pos = 0
    while True:
        if start_pos >= len(notation):
            break
        while not (end_pos >= len(notation) or notation[end_pos] in ',/'):
            end_pos += 1
        cursor = start_pos
        first_number_seen = False
        while cursor < end_pos:
            if notation[cursor] == '(':
                cursor = notation.find(')', cursor) + 1
                continue
            if notation[cursor] == '{':
                cursor = notation.find('}', cursor) + 1
                continue
            if notation[cursor] == '[':
                cursor = notation.find(']', cursor) + 1
                continue
            if notation[cursor].isdigit() and not first_number_seen: # Convert only if note start with 2367
                first_number_seen = True
                if not notation[cursor] in '2367':
                    break
            if notation[cursor].isdigit():
                notation = notation[:cursor] + inverse[notation[cursor]] + notation[cursor + 1:]
            cursor += 1
        start_pos = end_pos + 1
        end_pos = start_pos
    with open(path.splitext(filename)[0] + "_swapped" + path.splitext(filename)[1], 'w') as f:
        f.write(notation)

parser = argparse.ArgumentParser(prog="swap2367")
parser.add_argument("filename")
args = parser.parse_args()
swap2367(args.filename)
