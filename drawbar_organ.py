'''
Make a custom drawbar organ instrument for the CT-X3000/5000
'''

import os
import os.path
import struct
import textwrap
import sys

from internal.sysex_comms_internal import get_single_parameter, upload_ac7_internal, download_ac7_internal    #, set_single_parameter


#x = download_ac7_internal(0, memory=1, category=10)
#print(textwrap.fill(x.hex(" ").upper(), 48))



def get_length_of_parameter(param, category=10):
  if category!=10:
    raise Exception("Only supports category 10")
  if param < 0 or param > 34:
    raise Exception(f"Invalid parameter number for category 10: {param}")
  if param in [0,4,20,27,32]:
    return 2
  else:
    return 1

'''
Make a SYSEX message to set a single parameter in the CT-X
'''
def set_single_parameter_as_syx(param, data, category=10, memory=1, parameter_set=0, block0=0, block1=0, block2=0):
  ll = get_length_of_parameter(param, category)
  b = b'\xf0\x44\x19\x01\x7f\x01' + struct.pack("BBBB", category, memory, parameter_set%128, parameter_set//128) + b'\x00\x00' + struct.pack("BBBBBBBB", block2%128, block2//128, block1%128, block1//128, block0%128, block0//128, param%128, param//128) + b'\x00\x00\x00\x00'
  
  if ll == 3:
    b += struct.pack("BBB", data%128, data//128, data//(128*128))
  elif ll == 2:
    b += struct.pack("BB", data%128, data//128)
  elif ll == 1:
    b += struct.pack("B", data)
    
  b += b'\xf7'
  return b


  
  
sysex=[]




SPLITS = [
      0x19A,   # ride cymbal
      70,      # marimba
      1013,    # bass gtr
      1017     # organ wheel
 ]




## Category 7 ("Versatile" parameter set)::
##


#  PARAM    OFFSET
#  4          0x00    CAT12 pointer
#  5          0x02    minimum velocity
#  6          0x03    maximum velocity
#  7          0x04    minimum midi note
#  8          0x05    maximum midi note
#  9          0x06   usually 2. seems to affect stereo?
#  10-15      0x07    bitfields; see below



# Some basic set-up of the parameter set. Most of this is probably unnecessary
sysex.append(set_single_parameter_as_syx(0, 0x58))   # overall volume
sysex.append(set_single_parameter_as_syx(1, 0))
sysex.append(set_single_parameter_as_syx(2, 0))
sysex.append(set_single_parameter_as_syx(3, 0))
for i in range(24):
  splt = 0 # "Empty" value
  if i < len(SPLITS):
    splt = SPLITS[i]
    p_15 = 1
    
    
  if i < len(SPLITS)-1:
    q = 0x05
  elif i == len(SPLITS)-1:
    q = 0x1D
  else:
    q = 0x1F
    
  sysex.append(set_single_parameter_as_syx(4, splt, block0=i))
  sysex.append(set_single_parameter_as_syx(5, 0, block0=i))
  sysex.append(set_single_parameter_as_syx(6, 0x7F, block0=i))
  sysex.append(set_single_parameter_as_syx(7, 0, block0=i))
  sysex.append(set_single_parameter_as_syx(8, 0x7F, block0=i))
  sysex.append(set_single_parameter_as_syx(9, 0x70 if i == len(SPLITS)-1 else 0x02, block0=i))
  sysex.append(set_single_parameter_as_syx(10, 1 if (q & 0x40)!=0 else 0, block0=i))
  sysex.append(set_single_parameter_as_syx(11, 1 if (q & 0x20)!=0 else 0, block0=i))
  sysex.append(set_single_parameter_as_syx(12, 1 if (q & 0x10)!=0 else 0, block0=i))
  sysex.append(set_single_parameter_as_syx(13, 1 if (q & 0x08)!=0 else 0, block0=i))
  sysex.append(set_single_parameter_as_syx(14, 1 if (q & 0x04)!=0 else 0, block0=i))
  sysex.append(set_single_parameter_as_syx(15, (q & 0x03), block0=i))
sysex.append(set_single_parameter_as_syx(16, 0))
sysex.append(set_single_parameter_as_syx(17, 0x40))
sysex.append(set_single_parameter_as_syx(18, 0))
sysex.append(set_single_parameter_as_syx(19, 0))
sysex.append(set_single_parameter_as_syx(20, 0x80))
sysex.append(set_single_parameter_as_syx(21, 0x48))
sysex.append(set_single_parameter_as_syx(22, 0x48))
sysex.append(set_single_parameter_as_syx(23, 0))
sysex.append(set_single_parameter_as_syx(24, 0x40))
sysex.append(set_single_parameter_as_syx(25, 0))
sysex.append(set_single_parameter_as_syx(26, 0))
sysex.append(set_single_parameter_as_syx(27, 0x80))
sysex.append(set_single_parameter_as_syx(28, 0x40))
sysex.append(set_single_parameter_as_syx(29, 0x40))
sysex.append(set_single_parameter_as_syx(30, 0))
sysex.append(set_single_parameter_as_syx(31, 0))
sysex.append(set_single_parameter_as_syx(32, 0x80))
sysex.append(set_single_parameter_as_syx(33, 0x40))
sysex.append(set_single_parameter_as_syx(34, 0x40))








f_midi = os.open("/dev/midi1", os.O_RDWR)

for SYX in sysex:
  os.write(f_midi, SYX)


os.close(f_midi)



#x = download_ac7_internal(0, memory=1, category=10)
#print(textwrap.fill(x.hex(" ").upper(), 48))




#with open(os.path.join("..", "ac7-64", "CAT10_DATA", "11.bin"), "rb") as f1:
#  x =f1.read()
  
#upload_ac7_internal(0,x, memory=1, category=10)




if False:

  # The user tone number for the experimental data. 801-900
  #
  DEST = 801




  # Set up Category 3. Start with preset data 089 ("CLICK ORGAN")
  #
  with open(os.path.join("internal", "Data", "089CLICKORG.TON"), "rb") as f2:
    y = bytearray(f2.read()[0x20:-4])
  y[0x82:0x84] = struct.pack("<H", 30)
  y[0x10A:0x10C] = struct.pack("<H", 0)
  y[0x87] = 6
  y[0x10F] = 0
  y[0x1A6:0x1B2] = "Drawbar".ljust(12, " ").encode("ascii")

  upload_ac7_internal(DEST-801, bytes(y), memory=1, category=3)


sys.exit(0)



if sys.platform.startswith('linux') and not sys.stdout.isatty():
  # Stdout is a linux pipe. Write the output to it.
  for SYX in sysex:
    sys.stdout.buffer.write(SYX)
else:
  # Save to a file
  with open("88800000.syx", "wb") as f1:
    for SYX in sysex:
      f1.write(SYX)

