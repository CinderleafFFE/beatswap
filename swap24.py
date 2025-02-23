# 第二拍和第四拍互换 / 作者：绀霜
# 参数：文件名 BPM -o 偏移量

# Swap 2nd and 4th beat of each measure of a song
# Written by Sapfrost
# Args: filename bpm -o offset

import wave
import argparse

def swap24(filename: str, offset: float, bpm: float):
    the_file = wave.open(filename, 'rb')
    nchannels = the_file.getnchannels()
    sampwidth = the_file.getsampwidth()
    framewidth = nchannels * sampwidth
    framerate = the_file.getframerate()
    nframes = the_file.getnframes()
    the_file.rewind()
    data = bytearray(the_file.readframes(nframes))
    the_file.close()

    fpmeasure = framerate * 240 / bpm # The REAL frames per four-beat measure, fractional
    foffset = offset * framerate # Offset in frames

    # Calculate frames per beat
    # This number is only used for swapping within measure, Not for counting measures
    fpbeat = int(fpmeasure / 4)

    nmeasures = int((nframes - foffset) / fpmeasure) # Total measures to be swapped

    cb = bytearray(fpbeat * framewidth)
    pos = foffset
    for i in range(nmeasures):
        ipos = int(pos)

        # The swapping
        cb[:] = data[(ipos + fpbeat) * framewidth : (ipos + fpbeat * 2) * framewidth]
        data[(ipos + fpbeat) * framewidth : (ipos + fpbeat * 2) * framewidth] =\
              data[(ipos + fpbeat * 3) * framewidth : (ipos + fpbeat * 4) * framewidth]
        data[(ipos + fpbeat * 3) * framewidth : (ipos + fpbeat * 4) * framewidth] = cb[:]
        pos += fpmeasure

    the_file = wave.open("swapped_" + filename, 'wb')
    the_file.setnchannels(nchannels)
    the_file.setsampwidth(sampwidth)
    the_file.setframerate(framerate)
    the_file.setnframes(nframes)
    the_file.writeframes(data)
    the_file.close

parser = argparse.ArgumentParser(prog='swap24')
parser.add_argument('filename', type=str)
parser.add_argument('bpm', type=float)
parser.add_argument('-o', '--offset', type=float)
args = parser.parse_args()

filename = args.filename
bpm = args.bpm
offset = args.offset if args.offset else 0

swap24(filename, offset, bpm)
