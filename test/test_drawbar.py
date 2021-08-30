'''
Measure tonewheel frequencies
'''



import pyaudio
import os
import os.path
import struct
import time
import random
import shutil

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

import drawbar_organ




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


shutil.rmtree("RES")
os.mkdir("RES")


# Set capture volumes. This is highly dependent on audio setup.

os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(10000)) # Default = 3830, maximum=65536





# The user tone number for the experimental data. 801-900
#
DEST = 801




# Set up Category 3. Start with preset data 089 ("CLICK ORGAN")
#
with open(os.path.join("..", "internal", "Data", "089CLICKORG.TON"), "rb") as f2:
  y = bytearray(f2.read()[0x20:-4])
y[0x82:0x84] = struct.pack("<H", 30)
y[0x10A:0x10C] = struct.pack("<H", 0)
y[0x87] = 6
y[0x10F] = 0
y[0x1A6:0x1B2] = "---".ljust(12, " ").encode("ascii")

y[0x116] = 0x00   # no vibrato
y[0x1A5] = y[0x1A5] & 0xFE  # no DSP
for i in range(4):
  y[0x136+0x12*i:0x136+0x12*(i+1)] = b'\xff\x3f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # _really_ no DSP!

upload_ac7_internal(DEST-801, bytes(y), memory=1, category=3)




f_midi = os.open("/dev/midi1", os.O_RDWR)



# Set volume and pan in the keyboard. Writing this combination overrides the
# physical volume control, meaning this test should be repeatable.
os.write(f_midi, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00' + struct.pack('B', 33) + b'\xf7')
time.sleep(0.2)
os.write(f_midi, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7')
time.sleep(0.2)



os.write(f_midi, struct.pack("BBB", 0xB0, 123, 0))   # All Notes Off


SPLITS = [
      1310,  # fundamental
      742,   # 2nd harmonic
      1016,  # 6th harmonic
      1017   # sub-harmonic
    ]


# Open PyAudio for doing the recording

SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
RATE = 44100    # units of Hz. Probably only certain values are allowed, e.g.
                #  24000, 44100, 48000, 96000, ....
FRAMES = 1024


p = pyaudio.PyAudio()

NOTES = [60]

for COUNTER in range(1):
  
  
  random.shuffle(SPLITS)
  
  PARAM = random.choice([0,3] + list(range(16,  35)))
  

  plt.cla()
  
  
  for volume in [0x50, 0x60, 0x70, 0x7F]:

    sysexs = drawbar_organ.drawbar_sysex(SPLITS, params={PARAM: volume})
    for SYX in sysexs:
      os.write(f_midi, SYX)


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
      
      plt.semilogy(f, Px, label="PARAM:{0} = {1}".format(PARAM, volume))


  plt.xlim(0,3000)
  plt.ylim(1.E-10, 1.E-2)
  plt.xlabel('Frequency (Hz)')
  plt.ylabel('Power')
  
  
  
  plt.legend()

  
  midi_freq = 440. * numpy.power(2., (float(NOTE) - 69.)/12. )
  #peak_freq = f[ numpy.argmax(Px) ]
  #semitones = 12. * numpy.log2( peak_freq / midi_freq )
  #print("COUNT: {0} NOTE {1}:\tPeak frequency: {2:.5f} Hz (offset {3:.2f} semitones)".format(COUNTER, NOTE, peak_freq, semitones))
  
  d,u = plt.ylim()
  plt.semilogy([midi_freq, midi_freq], [4.5*d, 0.8*u], '-', c=matplotlib.colors.CSS4_COLORS['pink'])
  plt.title("[{0}, {1}, {2}, {3}], Midi NOTE: {4}".format(SPLITS[0], SPLITS[1], SPLITS[2], SPLITS[3], NOTE))
  
  #plt.show()
  plt.savefig(os.path.join("RES", "{1:04d}_{0}.png".format(NOTE, COUNTER)), format='png')
  plt.close()


p.terminate()




os.close(f_midi)

