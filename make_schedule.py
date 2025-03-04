#import re # The logic is too simple to use regex
import argparse
import os.path as path
import math
TICKS_PER_SEMIBREVE = 1536
TICKS_PER_BEAT = TICKS_PER_SEMIBREVE // 4

def fix_cross_beat_comma(overrun: int, orig_denom: int):
    orig_ticks_per_comma = TICKS_PER_SEMIBREVE // orig_denom
    good_denom = TICKS_PER_SEMIBREVE // math.gcd(overrun, orig_ticks_per_comma)
    good_comma_number = good_denom // orig_denom
    return good_comma_number, good_denom

def normalize_notation(notation: str):
    # In particular, if multiple markers occur in one comma, the final one is taken
    # Majdata seems to work properly only if markers are at the start of a comma
    new_commas = []
    for comma in notation.split(','):
        bpm = ""
        denom = None
        pos = 0
        new_comma = ""
        while pos < len(comma):
            # If bpm marker encountered
            if comma[pos] == '(':
                cl = comma.find(')', pos)
                bpm = comma[pos+1:cl]
                # Delete marker
                comma = comma[:pos] + comma[cl+1:]
                continue
            # If denominator marker encountered
            if comma[pos] == '{':
                cl = comma.find('}', pos)
                denom = int(comma[pos+1:cl])
                # Delete marker
                comma = comma[:pos] + comma[cl+1:]
                continue
            pos += 1
        if bpm != "":
            new_comma += f'({bpm})'
        if denom is not None:
            new_comma += f'{{{denom}}}'
        new_comma += comma
        new_commas.append(new_comma)
    return ','.join(new_commas)

def make_schedule(mai_filename: str, offset: float, list_beat_points: bool):
    f = open(mai_filename, 'r')
    notation = f.read()
    f.close()
    # Notation to be processed start at first bpm marker and ends at 'E'
    pos = notation.find('(')
    beat_start = pos # Mark start of first beat in notation
    bpm_sections = []
    chart_in_beats = []
    ticks_accum = 0
    ticks_per_comma = TICKS_PER_BEAT
    beat_init_bpm = ""
    beat_init_denom = 0

    # Main loop
    while pos < len(notation):
        # If end of notation encountered
        # Incomplete beat at the end is only added if notation is properly terminated with 'E'
        # Caution 'E' followed by a number does not signify end, but a Zone E touch note
        if notation[pos] == 'E' and (pos == len(notation) - 1 or not notation[pos+1].isdigit()):
            chart_in_beats.append(notation[beat_start:pos + 1])
            break
        # Check if full beat accumulated
        while ticks_accum >= TICKS_PER_BEAT:
            ticks_accum -= TICKS_PER_BEAT
            this_beat = notation[beat_start:pos]
            # Simplify if beat has only commas
            if all(c == ',' for c in this_beat):
                this_beat = '{4},'
            # Add bpm and denominator marker if not present
            # We assume the convention that bpm comes first
            #print("This beat: " + this_beat)
            if len(this_beat) == 0 or this_beat[0] != '{':
                this_beat = "{" + str(beat_init_denom) + "}" + this_beat
            if this_beat[0] != '(':
                this_beat = "(" + beat_init_bpm + ")" + this_beat
            chart_in_beats.append(this_beat)
            beat_start = pos
            beat_init_bpm  = bpm_sections[-1][0]
            beat_init_denom = denom
        # If bpm marker encountered
        if notation[pos] == '(':
            cl = notation.find(')', pos)
            # For now we'll keep bpm as string
            # It will be written in text anyways, and decimal fractions go ugly in float
            bpm = notation[pos+1:cl]
            # If bpm change is not at start of beat, take note to consider bad alignment
            if ticks_accum == 0:
                misalign = ""
            else:
                misalign = "%+d" % ticks_accum
            # Initialize beat initial bpm if first bpm marker
            if beat_init_bpm == "":
                beat_init_bpm = bpm
            bpm_sections.append([bpm, 0, misalign]) # Second entry is number of ticks in this bpm section
            pos = cl
        # If denominator marker encountered
        if notation[pos] == '{':
            cl = notation.find('}', pos)
            denom = int(notation[pos+1:cl])
            ticks_per_comma = TICKS_PER_SEMIBREVE // denom
            # Initialize beat initial denominator if first denominator marker
            if beat_init_denom == 0:
                beat_init_denom = denom
            pos = cl
        # If regular comma encountered
        if notation[pos] == ',':
            # Look ahead for cross beat comma
            ticks_before = ticks_accum
            ticks_after = ticks_accum + ticks_per_comma
            if ticks_after // TICKS_PER_BEAT > ticks_before // TICKS_PER_BEAT and (ticks_after % TICKS_PER_BEAT != 0 or denom < 4):
                print("Caution: comma cross beat boundary: " + str(ticks_before) + " -> " + str(ticks_accum))
                print(notation[beat_start:pos + 1] + " @ line " + str(notation.count('\n', 0, pos) + 1))
                overrun = ticks_after % TICKS_PER_BEAT + TICKS_PER_BEAT # If comma ends on beat, fix resolution to one beat
                good_comma_number, good_denom = fix_cross_beat_comma(overrun, denom)
                comma_fix = f'{{{good_denom}}}' + ',' * good_comma_number + f'{{{denom}}}'
                notation = notation[:pos] + comma_fix + notation[pos+1:]
                denom = good_denom
                ticks_per_comma = TICKS_PER_SEMIBREVE // denom
                print("Fixed to: " + notation[pos:pos + len(comma_fix)])
                pos = notation.find('}', pos) + 1 # Move cursor to just after denominator marker
            ticks_accum += ticks_per_comma
            bpm_sections[-1][1] += ticks_per_comma
        pos += 1
        
    # List bpm sections in ticks, just in case for reference
    f = open(path.splitext(mai_filename)[0] + "_sections.txt", 'w')
    for bpm_section in bpm_sections:
        f.write(f'{bpm_section[0]} {bpm_section[1]} {bpm_section[2]}\n')
    f.close()
    
    if list_beat_points:
        # List beat points
        f = open(path.splitext(mai_filename)[0] + "_beatpoints.txt", 'w')
        beatpoints = [offset]
        curr_time = offset
        ticks_excess = 0
        for bpm_section in bpm_sections:
            ticks_remaining = bpm_section[1]
            first_beat = True
            if ticks_remaining + ticks_excess >= TICKS_PER_BEAT: # Only enter loop if a full beat can be made
                ticks_remaining += ticks_excess
                while ticks_remaining >= TICKS_PER_BEAT: # If ticks left in section makes at least one full beat
                    if first_beat:  # First beat in section might be partial
                        curr_time += 60 / float(bpm_section[0]) * (TICKS_PER_BEAT - ticks_excess) / TICKS_PER_BEAT
                        first_beat = False
                        ticks_excess = 0
                    else:
                        curr_time += 60 / float(bpm_section[0])
                    ticks_remaining -= TICKS_PER_BEAT
                    beatpoints.append(curr_time)
            curr_time += 60 / float(bpm_section[0]) * ticks_remaining / TICKS_PER_BEAT # Advance time by remaining ticks
            ticks_excess += ticks_remaining
        for beatpoint in beatpoints:
            f.write(f'{beatpoint}\n')
        f.close()

        # Write beat delimited chart
        f = open(path.splitext(mai_filename)[0] + "_beatchart.txt", 'w')
        for chart_in_beat in chart_in_beats:
            chart_in_beat = "".join(chart_in_beat.split()) # Since delimiter is newline, purge newline
            chart_in_beat = normalize_notation(chart_in_beat)
            #print("Writing chart line: " + chart_in_beat)
            f.write(chart_in_beat + '\n')

parser = argparse.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('-o', '--offset', type=float)
parser.add_argument('-b', '--list-beat-points', action='store_true')
args = parser.parse_args()
if args.offset is None:
    args.offset = 0
make_schedule(args.filename, args.offset, args.list_beat_points)
