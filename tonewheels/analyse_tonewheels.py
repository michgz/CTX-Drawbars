'''
Measure tonewheel frequencies
'''



import pyaudio
import os
import os.path
import struct
import time

from scipy.signal import decimate, hilbert, stft, chirp, welch
import numpy
import matplotlib.pyplot as plt
import matplotlib
import textwrap
import pickle
import itertools

import sys

# We're importing from a sibling directory.
sys.path.append('..')
sys.path.append('../internal')


from internal.sysex_comms_internal import get_single_parameter, upload_ac7_internal, download_ac7_internal    #, set_single_parameter



if not sys.platform.startswith('linux'):
  raise Exception("Terminating. This is an investigative script that probably needs Linux in order to work correctly.")


pulse_device_index = None

p = pyaudio.PyAudio()

for i in range(p.get_device_count()):
  d = p.get_device_info_by_index(i)
  if d['name'] == 'pulse' and d['maxInputChannels'] >= 1:
    pulse_device_index = i
    break

p.terminate()

if pulse_device_index is None:
  raise Exception("Terminating. Could not find pulseAudio as an input device")




# Set capture volumes. This is highly dependent on audio setup.

os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(10000)) # Default = 3830, maximum=65536





# The following are the Category 12 ("Split") numbers that sound like monophonic tonewheel
# recordings in a CT-X3000 (probably also CT-X5000).
#
CAT12_VALUES = list(range(73,78)) + [726,727,729,742] + list(range(1012,1025)) + list(range(1030,1032))



# The user tone number for the experimental data. 801-900
#
DEST = 801




# Set up Category 3. Start with preset data 089 ("CLICK ORGAN")
#
with open(os.path.join("..", "internal", "Data", "089CLICKORG.TON"), "rb") as f2:
  y = bytearray(f2.read()[0x20:-4])
y[0x82:0x84] = struct.pack("<H", 900)
y[0x10A:0x10C] = struct.pack("<H", 900)
y[0x87] = 0
y[0x10F] = 0
y[0x1A6:0x1B2] = "---".ljust(12, " ").encode("ascii")

y[0x116] = 0x00   # no vibrato
y[0x1A5] = y[0x1A5] & 0xFE  # no DSP
for i in range(4):
  y[0x136+0x12*i:0x136+0x12*(i+1)] = b'\xff\x3f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # _really_ no DSP!

upload_ac7_internal(DEST-801, bytes(y), memory=1, category=3)



# Set up Category 5. Start with preset data 290 ("CLICK ORGAN", used by category
# 3 tone 089).
#
with open(os.path.join("..", "internal", "Data", "CAT5_290.bin"), "rb") as f2:
  z = bytearray(f2.read())
for i in range(8):
  if i == 0:
    u = 0x1CF
  else:
    u = 0
  z[0+i*6:2+i*6] = struct.pack("<H", u)
  z[2+i*6] = 0     #min velocity
  z[3+i*6] = 0x7f  # max velocity
  z[4+i*6] = 0     # min midi note
  z[5+i*6] = 0x7f  # max midi note
  
upload_ac7_internal(0, bytes(z), memory=1, category=5)


#   Param   Offset   Meaning
#     0      0x42
#     1
#     2
#     3      0x43
#     4      0x00     Category 12 index
#     5      0x02     Minimum velocity
#     6      0x03     Maximum velocity
#     7      0x04     Minimum MIDI note
#     8      0x05     Maximum MIDI note
#     9
#    10      0x30
#    11      0x31
#    12      0x32
#    13      0x33
#    14      0x34
#    15      0x35
#    16      
#    17      0x36
#    18      0x37
#    19      0x38
#    20      0x39
#    21      0x3A
#    22      0x3B
#    23      0x3C
#    24      0x3D
#    25      0x3E
#    26      0x3F
#    27      



def get_param_length(param, category=5):
  
  if category != 5:
    raise Exception("Only category 5 is implemented so far!")
  
  if param > 27:
    raise Exception("Invalid parameter number for category 5")
  
  if param in [0, 4, 13, 20, 25]:
    return 2
  return 1



f_midi = os.open("/dev/midi1", os.O_RDWR)



# Set volume and pan in the keyboard. Writing this combination overrides the
# physical volume control, meaning this test should be repeatable.
os.write(f_midi, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00' + struct.pack('B', 33) + b'\xf7')
time.sleep(0.2)
os.write(f_midi, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7')
time.sleep(0.2)



def set_single_parameter(pp, data, category=5, memory=1, parameter_set=0, block0=0,block1=0,block2=0):
  
  global f_midi
  
  
  b = b'\xF0\x44\x19\x01\x7F\x01' + struct.pack("BBBB", category, memory, parameter_set%128, parameter_set//128) + b'\x00\x00\x00\x00' + struct.pack("<HHHHH", block1, block0, pp, 0, 0)
  
  if get_param_length(pp) == 2:
    b += struct.pack("BB", data%128, data//128)
  else:
    try:
      b += struct.pack("B", data)
    except:
      print(f"pp={pp}")
      print(f"data={data}")
  b += b'\xF7'
  
  os.write(f_midi, b)



os.write(f_midi, struct.pack("BBB", 0xB0, 123, 0))   # All Notes Off


# Open PyAudio for doing the recording

SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
RATE = 44100    # units of Hz. Probably only certain values are allowed, e.g.
                #  24000, 44100, 48000, 96000, ....
FRAMES = 1024


p = pyaudio.PyAudio()

NOTES = [40, 60, 72]

for CAT12 in CAT12_VALUES:
  
  set_single_parameter(4, CAT12, memory=1, category=5)
  
  print(CAT12)


  os.write(f_midi, struct.pack("8B", 0xB0, 0x00, 65, 0xB0, 0x20, 0, 0xC0, DEST-801))

  for NOTE in NOTES:   # Try at various different pitches
    time.sleep(0.2)
    os.write(f_midi, struct.pack("3B", 0x90, NOTE, 0x7F))
    time.sleep(0.2)

    x = p.open(format=pyaudio.paFloat32,
                channels=2,
                rate=RATE,
                input=True,
                input_device_index=pulse_device_index,
                start=True,
                frames_per_buffer=FRAMES)
    frame_count = 32*1024  # approx 1 second
    v = x.read(frame_count)
    x.close()

    result = numpy.frombuffer(v, dtype=numpy.float32)
    result = numpy.reshape(result, (frame_count, 2))
    result = result[:, 0]
    


    os.write(f_midi, struct.pack("3B", 0x80, NOTE, 0x7F))
    time.sleep(0.6)
    
    f, Px = welch(result, fs=RATE, nperseg = 2*1024)
    
    plt.figure()
    plt.semilogy(f, Px)
    plt.xlim(0,6000)
    plt.ylim(1.E-12, 1.E-6)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Power')
    
    midi_freq = 440. * numpy.power(2., (float(NOTE) - 69.)/12. )
    peak_freq = f[ numpy.argmax(Px) ]
    semitones = 12. * numpy.log2( peak_freq / midi_freq )
    print("CAT 12: {0} NOTE {1}:\tPeak frequency: {2:.5f} Hz (offset {3:.2f} semitones)".format(CAT12, NOTE, peak_freq, semitones))
    
    plt.semilogy([midi_freq, midi_freq], [4.5E-12, 8.E-7], '-', c=matplotlib.colors.CSS4_COLORS['pink'])
    plt.title("SPLIT: {0}, Midi NOTE: {1}".format(CAT12, NOTE))
    
    plt.legend(['Measured', 'Nominal tonic'])
    
    #plt.show()
    plt.savefig("{1:04d}_{0}.png".format(NOTE, CAT12), format='png')
    plt.close()


p.terminate()




os.close(f_midi)

