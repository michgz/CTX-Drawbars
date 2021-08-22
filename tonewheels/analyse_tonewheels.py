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
import textwrap
import pickle
#from fitting import fitting
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






# The following are the Category 12 ("Split") numbers that sound like monophonic tonewheel
# recordings in a CT-X3000 (probably also CT-X5000).
#
CAT12_VALUES = [1015,1016,1017,1019,1020,1021,1022,1027,1029,1030,1031,1033]


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


for CAT12 in CAT12_VALUES:
  
  set_single_parameter(4, CAT12, memory=1, category=5)


  os.write(f_midi, struct.pack("8B", 0xB0, 0x00, 65, 0xB0, 0x20, 0, 0xC0, DEST-801))

  for NOTE in [36, 60, 84]:   # Three octaves of "C"
    time.sleep(0.2)
    os.write(f_midi, struct.pack("3B", 0x90, NOTE, 0x7F))
    time.sleep(1.0)
    os.write(f_midi, struct.pack("3B", 0x80, NOTE, 0x7F))
    time.sleep(0.6)
    




os.close(f_midi)


sys.exit(0)



with open("Envelope.csv", "a") as f7:
  
  f7.write("\nStart time (s),Time delta (s),Y delta,Lambda,Max,Cat3 Time Param 2,Cat12 Time Param 2,Ampl 1,Ampl 2,Velocity\n")






# Set the raw MIDI device name to use.
DEVICE_NAME = '/dev/midi1'



# First, set capture volumes. This is highly dependent on audio setup. It works
# on my machine (Ubuntu 18.04)


# There is a choice to set in pulseaudio or ALSA. They seem to override each other, so only do one:
#if False:
#  os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(3830)) # Default = 3830, maximum=65536
#else:
#  os.system("amixer -c 0 cset iface=MIXER,name='Capture Volume',index=1 {0}".format(35)) # Default = 46, maximum=46
#  #os.system("amixer -c 0 cset iface=MIXER,name='Line Boost Volume',index=1 {0}".format(0)) # Default = 0, maximum=3


os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(10000)) # Default = 3830, maximum=65536



with open(os.path.join("..", "calibration tones", "CAL1KHZ.TON"), "rb") as f1:
  x_3 = bytearray(f1.read()[0x20:-4])
with open(os.path.join("..", "CAT5_DATA", "3.bin"), "rb") as f1:
  x_5 = bytearray(f1.read())
with open(os.path.join("..", "CAT12_DATA", "5.bin"), "rb") as f1:
  x_12 = f1.read()
  


for i in range(8):
  x_5[i*6+0:i*6+2] = struct.pack("<H", 1500 if i == 0 else 0)


#x_5[0x30:0x46] = b'\x00'*0x16

upload_ac7_internal(0, bytes(x_5), memory=1, category=5)
upload_ac7_internal(0, x_12, memory=1, category=12)



x_3[0x82:0x84] = struct.pack("<H", 900)
x_3[0x10A:0x10C] = struct.pack("<H", 900)


upload_ac7_internal(0, bytes(x_3), memory=1, category=3)


# Open MIDI

f = os.open(DEVICE_NAME, os.O_RDWR)





# An alternative version
def set_single_parameter(p, x, category=3, memory=3, block0=0, block1=0, parameter_set=32):
  
  global f
  
  length_of_parameter = 1
  
  if category == 3:
    if p >= 6 and p <= 20 and p != 16:
      length_of_parameter = 2
      
    if p == 2 or p == 22:
      length_of_parameter = 2
  elif category == 12:
    if p >= 49 and p <= 56:
      length_of_parameter = 2
  
  b = b'\xf0\x44\x19\x01\x7F\x01' + struct.pack('BBBB', category, memory, parameter_set%128, parameter_set//128) + b'\x00\x00\x00\x00' + struct.pack('BBBBBB', block1%128, block1//128, block0%128, block0//128, p%128, p//128) + b'\x00\x00\x00\x00'
  
  if length_of_parameter == 2:
    b += struct.pack('BB', x%128, x//128)
  else:
    b += struct.pack('B', x)
  b += b'\xf7'
  
  os.write(f, b)
  
  
  




# Set volume and pan in the keyboard. Writing this combination overrides the
# physical volume control, meaning this test should be repeatable.
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00' + struct.pack('B', 33) + b'\xf7')
time.sleep(0.2)
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7')
time.sleep(0.2)







VOL_SCALE = 0x7f
ATTACK_TIME_2 = 0x1C0
ATTACK_TIME_SCALE_2 = 0x190
AMPL_1 = 0x80
AMPL_2 = 0x20
VELOCITY = 0x7F

for VOLUME in list(range(8,128,8)) + [0x7f]:




  # Set the tone. 82/63 = 1kHz tone
  BANK_MSB = 65
  PATCH = 0



  os.write(f, struct.pack('BBBBBBBB', 0xB0, 0, BANK_MSB, 0xB0, 0x20, 0, 0xC0, PATCH))
  time.sleep(0.2)


  set_single_parameter(19, 0x60, block0=0)
  set_single_parameter(19, AMPL_1, block0=1)
  set_single_parameter(19, AMPL_2, block0=2)
  set_single_parameter(19, 0x68, block0=3)
  set_single_parameter(19, 0x68, block0=4)
  set_single_parameter(19, 0x00, block0=5)
  set_single_parameter(19, 0x00, block0=6)
  
  
  set_single_parameter(45, VOLUME)

  set_single_parameter(20, 0x1E0, block0=0)
  set_single_parameter(20, 0x200, block0=1)
  set_single_parameter(20, ATTACK_TIME_2, block0=2)
  
  

  set_single_parameter(56, ATTACK_TIME_SCALE_2, block0=0, block1=2, category=12, memory=1, parameter_set=0)
  set_single_parameter(27, VOL_SCALE, category=12, memory=1, parameter_set=0)
  
  




  time.sleep(0.2)


  SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
  RATE = 44100    # units of Hz. Probably only certain values are allowed, e.g.
                  #  24000, 44100, 48000, 96000, ....
  FRAMES = 1024

  mm = 0
  lx = ()

  def callback_audio(in_data,      # recorded data if input=True; else None
           frame_count,  # number of frames
           time_info,    # dictionary
           status_flags):
    global mm
    global lx
    
    
    #print(textwrap.fill(in_data[0:500].hex(" ").upper(), 48))
    
    
    #print(f"Frame count = {frame_count}")
    #print(f"in_data len = {len(in_data)}")
    
    result = numpy.frombuffer(in_data, dtype=numpy.float32)
    
    #print(f"frombuffer size = {numpy.size(result)}")
    #print(f"frombuffer shape = {numpy.shape(result)}")
    
    result = numpy.reshape(result, (frame_count, 2))
    

    #print(f"  frombuffer size = {numpy.size(result)}")
    #print(f"  frombuffer shape = {numpy.shape(result)}")



    result = result[:, 0]
    #print(f"  frombuffer size = {numpy.size(result)}")
    #print(f"  frombuffer shape = {numpy.shape(result)}")

    #w = 0
    #while w+4 <= len(in_data):
    #  (l, r) = struct.unpack('<2h', in_data[w:w+4]) # left & right samples
    #  lx.append(l)
    #  w += 4
    
    #print(lx)
    #print(result)
    
    #lx += (in_data, )
    
    #result = decimate(numpy.abs(hilbert(result)), 480, ftype='fir')
    
    lx += (result, )
    
    #lx.append(result)
    
    if frame_count != FRAMES:
      raise Exception("Expecting frame of {0}, got {1}".format(FRAMES, frame_count))
    
    if status_flags != 0:
      raise Exception("Flags {0}. Total frames so far: {1}".format(status_flags, len(lx)))
    
    #print(len(lx))
    
    
    mm += 1
    
    if mm >= 14*12:
      return (None, pyaudio.paComplete)
    
    return (None, pyaudio.paContinue)






  p = pyaudio.PyAudio()

  x = p.open(format=pyaudio.paFloat32,
              channels=2,
              rate=RATE,
              input=True,
              input_device_index=16,
              start=False,
              frames_per_buffer=FRAMES,
              stream_callback=callback_audio)


  print(f"Input latency = {x.get_input_latency()}")

  for nn in [60]:


    x.start_stream()

    time.sleep(0.5)

    # MIDI note on
    os.write(f, b'\x90' + struct.pack('B', nn) + struct.pack("B", VELOCITY))



    time.sleep(2.6)



    # MIDI note off
    os.write(f, b'\x80' + struct.pack('B', nn) + b'\x7f')
    time.sleep(0.5)




    x.stop_stream()


  if False:

    llx = ( )

    for in_data in lx:

      result = numpy.frombuffer(in_data, dtype=numpy.float32)
      result = numpy.reshape(result, (FRAMES, 2))
      result = result[:, 0]
      llx += (result, )




  lx = (numpy.concatenate(lx))


  # Get the "amplitude" of the recorded signal
  #dx = numpy.argmax(numpy.abs(stft(lx, nperseg=1024)[2]), axis=1)
  ex = decimate(numpy.abs(hilbert(lx)), 480, ftype='fir')
  #gx = []



  xx = numpy.linspace(0, len(ex)*(480./float(RATE)), len(ex))
  #print(xx)

  val = {'x': xx, 'y': ex}





  # Finished. Tidy everything up.


  x.close()

  p.terminate()

  #plt.plot(ex)
  #plt.show()




  cc = fitting(val)

  x_lst = os.listdir("Plots")
  for i in itertools.count(1):
    
    if not "{0}.bin".format(i) in x_lst:
      
      break


  with open(os.path.join("Plots", '{0}.bin'.format(i)), 'wb') as f5:
    pickle.dump(val, f5)


  with open("EnvelopeLog.txt", "a") as f6:
    
    f6.write(str(os.path.join("Plots", '{0}.bin'.format(i))) + ":\n")
    f6.write("  Attack time 2 = 0x{0:02X} ,  Attack scale 2 = 0x{1:03X}\n".format(ATTACK_TIME_2, ATTACK_TIME_SCALE_2))
    f6.write("  " + str(cc) + "\n\n")
    
    
  with open("Envelope.csv", "a") as f7:
    
    f7.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}\n".format(cc['t1'],cc['delta_t'],cc['delta_y'],cc['lambda'],cc['max'],ATTACK_TIME_2, ATTACK_TIME_SCALE_2, AMPL_1, AMPL_2, VELOCITY,VOLUME))
    
    
os.close(f)




