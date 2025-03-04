import wave
import argparse
import os.path as path

def swap24_scheduled(wav_filename: str, mai_filename: str, beatpoints_filename: str, swap_pattern: list, fps: float):
    # Chart file is supposed to be already beat delimited

    meter = len(swap_pattern)
    with wave.open(wav_filename, 'rb') as wav:
        nchannels, sampwidth, framerate, nframes, comptype, compname = wav.getparams()
        framewidth = nchannels * sampwidth
        data = wav.readframes(nframes)
    
    with open(mai_filename, 'r') as chart:
        chart_lines = chart.readlines()

    with open(beatpoints_filename, 'r') as beatpoints_file:
        beatpoints = []
        for line in beatpoints_file.readlines():
            beatpoints.append(float(line))

    # Number of beats to be swapped is determined by least of beats in beat points file and chart
    beats = min(len(beatpoints) - 1, len(chart_lines))
    bars = beats // meter
    
    out_data = bytearray(nframes * framewidth)
    out_chart_lines = []
    lookup = [] # Video frames lookup
    # Copy audio and video before first beat as-is
    out_data[:int(beatpoints[0] * framerate * framewidth)] = data[:int(beatpoints[0] * framerate * framewidth)]
    for i in range(int(beatpoints[0] * fps)):
        lookup.append(i)
    # For technical simplicity, chart is supposed to start at beat one of bar
    # Swapping starts
    for i in range(bars):
        for j in range(meter):
            dst_beat = i * meter + j
            src_beat = i * meter + swap_pattern[j]
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
            out_chart_lines.append(chart_lines[src_beat])
    # Copy audio and video after last beat as-is
    out_data[int(beatpoints[-1] * framerate * framewidth):] = data[int(beatpoints[-1] * framerate * framewidth):]
    for i in range(int(beatpoints[-1] * fps), int(nframes / framerate * fps) + 1):
        lookup.append(i)
    # Copy remaining chart lines, if any
    out_chart_lines += chart_lines[bars * meter:]

    # Write audio
    with wave.open(path.splitext(wav_filename)[0] + "_swapped" + path.splitext(wav_filename)[1], 'wb') as wav:
        wav.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
        wav.writeframes(out_data)

    # Write lookup
    lookup_file = open(path.splitext(wav_filename)[0] + "_lookup.js", 'w')
    lookup_file.write("var lookup = [")
    for i in range(len(lookup) - 1):
        lookup_file.write(str(lookup[i]) + ", ")
    lookup_file.write(str(lookup[-1]) + "];\n")
    lookup_file.write("framesToTime(lookup[timeToFrames(time + 1e-6)]) + 1e-6;\n")
    lookup_file.close()

    # Write chart
    with open(path.splitext(mai_filename)[0] + "_swapped" + path.splitext(mai_filename)[1], 'w') as chart:
        chart.writelines(out_chart_lines)

parser = argparse.ArgumentParser(prog='swap24_scheduled')
parser.add_argument('wav_filename', type=str)
parser.add_argument('mai_filename', type=str)
parser.add_argument('beatpoints_filename', type=str)
parser.add_argument('swap_pattern_str', type=str)
parser.add_argument('fps', type=float)
args = parser.parse_args()
swap_pattern = [int(x) for x in args.swap_pattern_str.split(',')]
swap24_scheduled(args.wav_filename, args.mai_filename, args.beatpoints_filename, swap_pattern, args.fps)
