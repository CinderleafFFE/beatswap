import wave
import argparse
import os.path as path

def swap24_scheduled(filename: str, schedule_filename: str):
    # Read schedule
    schedule = []
    schedule_file = open(schedule_filename, 'r')
    lines = schedule_file.readlines()

    # Get offset
    if lines[0][0 : 7] != "offset ":
        raise Exception("First line must be offset")
    else:
        offset = float(lines[0][7 :])

    # Get swapping pattern
    if lines[1][0 : 9] != "swapping ":
        raise Exception("Second line must be swapping")
    else:
        swapping = []
        for s in lines[1][9 :].split():
            swapping.append(int(s))

    # Get fps
    if lines[2][0 : 4] != "fps ":
        raise Exception("Third line must be fps")
    else:
        fps = float(lines[2][4 :])

    # Process rest of schedule
    # Tuple of bpm and number of beats
    for line in lines[3 :]:
        my_tuple = line.split()
        if len(my_tuple) == 2:
            schedule.append((float(my_tuple[0]), int(my_tuple[1])))

    schedule_file.close()

    # Write beat points
    beatpoints = [offset]
    for t in schedule:
        for j in range(t[1]):
            if t[0] != 0:
                beatpoints.append(beatpoints[-1] + 60 / t[0])
            else: # bpm zero means time zero
                beatpoints.append(beatpoints[-1])

    meter = len(swapping)
    if (len(beatpoints) - 1) % meter != 0:
        raise Exception("Meter (swapping cycle length) must divide total beats")
    bars = (len(beatpoints) - 1) // meter

    # Read audio
    the_file = wave.open(filename, 'rb')
    nchannels = the_file.getnchannels()
    sampwidth = the_file.getsampwidth()
    framewidth = nchannels * sampwidth
    framerate = the_file.getframerate()
    nframes = the_file.getnframes()
    the_file.rewind()
    data = the_file.readframes(nframes)
    the_file.close()

    # Audio and lookup buffer
    out_data = bytearray(nframes * framewidth)
    lookup = []

    # Copy content before first beat
    first_beat_af = int(beatpoints[0] * framerate)
    first_beat_vf = int(beatpoints[0] * fps)
    out_data[0 : first_beat_af * framewidth] = data[0 : first_beat_af * framewidth]
    for i in range(first_beat_vf):
        lookup.append(i)
    
    # Swapping starts since first beat i.e. first bar
    for i in range(bars):
        for j in range(meter):
            dst_beat = i * meter + j
            src_beat = i * meter + swapping[j]
            dst_beat_start_af = int(beatpoints[dst_beat] * framerate)
            dst_beat_end_af = int(beatpoints[dst_beat + 1] * framerate)
            dst_beat_start_vf = int(beatpoints[dst_beat] * fps)
            dst_beat_end_vf = int(beatpoints[dst_beat + 1] * fps)
            src_beat_start_af = int(beatpoints[src_beat] * framerate)
            src_beat_end_af = int(beatpoints[src_beat + 1] * framerate)
            src_beat_start_vf = int(beatpoints[src_beat] * fps)
            src_beat_end_vf = int(beatpoints[src_beat + 1] * fps)
            out_data[dst_beat_start_af * framewidth : dst_beat_end_af * framewidth] = \
                data[src_beat_start_af * framewidth : src_beat_end_af * framewidth]
            lookup += list(range(src_beat_start_vf, src_beat_end_vf))
    
    # Copy content after last beat
    last_beat_af = int(beatpoints[-1] * framerate)
    last_beat_vf = int(beatpoints[-1] * fps)
    song_end_af = nframes
    song_end_vf = int(nframes / framerate * fps) + 1
    out_data[last_beat_af * framewidth : song_end_af * framewidth] = \
        data[last_beat_af * framewidth : song_end_af * framewidth]
    for i in range(last_beat_vf, song_end_vf):
        lookup.append(i)

    # Write audio
    the_file = wave.open(path.splitext(filename)[0] + "_swapped" + path.splitext(filename)[1], 'wb')
    the_file.setnchannels(nchannels)
    the_file.setsampwidth(sampwidth)
    the_file.setframerate(framerate)
    the_file.setnframes(nframes)
    the_file.writeframes(out_data)
    the_file.close()

    # Write lookup
    lookup_file = open(path.splitext(filename)[0] + "_lookup.js", 'w')
    lookup_file.write("var lookup = [")
    for i in range(len(lookup) - 1):
        lookup_file.write(str(lookup[i]) + ", ")
    lookup_file.write(str(lookup[-1]) + "];\n")
    lookup_file.write("framesToTime(lookup[timeToFrames(time + 1e-6)]) + 1e-6;\n")
    lookup_file.close()

parser = argparse.ArgumentParser(prog='swap24_scheduled')
parser.add_argument('filename', type=str)
parser.add_argument('schedule_filename', type=str)
args = parser.parse_args()
swap24_scheduled(args.filename, args.schedule_filename)
