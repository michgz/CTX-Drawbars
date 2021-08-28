'''
Make a custom drawbar organ instrument for the CT-X3000/5000
'''

import os
import os.path
import struct
import textwrap
import sys

from internal.sysex_comms_internal import get_single_parameter, upload_ac7_internal, download_ac7_internal    #, set_single_parameter




## Category 7 ("Piano" parameter set)::
##


#  PARAM      OFFSET    BITS     BYTES
#    0        0x401E      4        1
#    1        0x401F      4        1
#    2         0x02       7        1
#    3         0x00      16        3
#    4       0x2007 (bit ?)   1    1
#    5       0x2007 (bit ?)   1    1
#    6        0x2004      8        2     Block0+0x2004
#    7        0x2005      7        1     Block0+0x2004
#    8        0x2006      7        1     Block0+0x2004
#    9         0x06       7        1     Block0+0x2004      Block1+0x40      Block2+0x08
#   10         0x07       7        1     Block0+0x2004      Block1+0x40      Block2+0x08
#   11         0x04      14        2     Block0+0x2004      Block1+0x40      Block2+0x08
#   12         0x08       8        2     Block0+0x2004      Block1+0x40      Block2+0x08
#   13         0x09       8        2     Block0+0x2004      Block1+0x40      Block2+0x08
#   14         0x0A       7        1     Block0+0x2004      Block1+0x40      Block2+0x08
#   15        0x401D (bits 4-7)  4  1



#  PARAM      OFFSET     BITS
#    16        0x400C       7        1
#    17        0x400D       7        1
#    18        0x400E       7        1
#    19        0x400F       8        2
#    20        0x4010       7        1
#    21        0x4011       7        1
#    22        0x401D (bits 0-3) 4    1
#    23        0x4012       7        1
#    24        0x4013       7        1
#    25        0x4014       7        1
#    26        0x4015       8        2
#    27        0x4016       7        1
#    28        0x4017       7        1
#    29        0x4018       7        1
#    30        0x4019       7        1
#    31        0x401A       8        2
#    32        0x401B       7        1
#    33        0x401C       7        1





def get_length_of_parameter(param, category=7):
  if category!=7:
    raise Exception("Only supports category 7")
  if param < 0 or param > 33:
    raise Exception(f"Invalid parameter number for category 7: {param}")
  if param == 3:
    return 3
  elif param in [6, 11, 12, 13, 19, 26, 31]:
    return 2
  else:
    return 1

'''
Make a SYSEX message to set a single parameter in the CT-X
'''
def set_single_parameter_as_syx(param, data, category=7, memory=1, parameter_set=0, block0=0, block1=0, block2=0):
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


# Some basic set-up of the parameter set. Most of this is probably unnecessary
sysex.append(set_single_parameter_as_syx(0, 8))
sysex.append(set_single_parameter_as_syx(1, 8))
sysex.append(set_single_parameter_as_syx(2, 0x40))
sysex.append(set_single_parameter_as_syx(3, 0))
sysex.append(set_single_parameter_as_syx(4, 1, block0=0))
sysex.append(set_single_parameter_as_syx(5, 0, block0=0))
sysex.append(set_single_parameter_as_syx(4, 0, block0=1))
sysex.append(set_single_parameter_as_syx(5, 0, block0=1))
sysex.append(set_single_parameter_as_syx(6, 0x60, block0=0))
sysex.append(set_single_parameter_as_syx(7, 0x40, block0=0))
sysex.append(set_single_parameter_as_syx(8, 0x02, block0=0))
sysex.append(set_single_parameter_as_syx(6, 0x60, block0=1))
sysex.append(set_single_parameter_as_syx(7, 0x40, block0=1))
sysex.append(set_single_parameter_as_syx(8, 0x02, block0=1))
sysex.append(set_single_parameter_as_syx(15, 0))
sysex.append(set_single_parameter_as_syx(16, 0x40))
sysex.append(set_single_parameter_as_syx(17, 0x40))
sysex.append(set_single_parameter_as_syx(18, 0x40))
sysex.append(set_single_parameter_as_syx(19, 0x80))
sysex.append(set_single_parameter_as_syx(20, 0x4A))
sysex.append(set_single_parameter_as_syx(21, 0x4A))
sysex.append(set_single_parameter_as_syx(22, 0))
sysex.append(set_single_parameter_as_syx(23, 0x40))
sysex.append(set_single_parameter_as_syx(24, 0x40))
sysex.append(set_single_parameter_as_syx(25, 0x40))
sysex.append(set_single_parameter_as_syx(26, 0x80))
sysex.append(set_single_parameter_as_syx(27, 0x40))
sysex.append(set_single_parameter_as_syx(28, 0x40))
sysex.append(set_single_parameter_as_syx(29, 0x40))
sysex.append(set_single_parameter_as_syx(30, 0x40))
sysex.append(set_single_parameter_as_syx(31, 0x80))
sysex.append(set_single_parameter_as_syx(32, 0x40))
sysex.append(set_single_parameter_as_syx(33, 0x40))


TONES = [(1017,120),(1013,120), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]


for B0 in [0]:
  for B1 in [60]:
    for B2 in range(8):
      splt = TONES[B2][0]
      sysex.append(set_single_parameter_as_syx(11, splt, block0=B0, block1=B1, block2=B2))  # "Split"

      if splt != 0:
        sysex.append(set_single_parameter_as_syx(9, 0x00, block0=B0, block1=B1, block2=B2))   # lowest MIDI note
        sysex.append(set_single_parameter_as_syx(10, 0x7F, block0=B0, block1=B1, block2=B2))  # highest MIDI note
        sysex.append(set_single_parameter_as_syx(12, TONES[B2][1], block0=B0, block1=B1, block2=B2))  # volume
        sysex.append(set_single_parameter_as_syx(13, 0x80, block0=B0, block1=B1, block2=B2))  # pan
        sysex.append(set_single_parameter_as_syx(14, 2, block0=B0, block1=B1, block2=B2))     # ??  




if False:
  # This is for testing only.


  f_midi = os.open("/dev/midi1", os.O_RDWR)

  for SYX in sysex:
    os.write(f_midi, SYX)


  os.close(f_midi)




  # The user tone number for the experimental data. 801-900
  #
  DEST = 801




  # Set up Category 3. Start with preset data 089 ("CLICK ORGAN")
  #
  with open(os.path.join("internal", "Data", "089CLICKORG.TON"), "rb") as f2:
    y = bytearray(f2.read()[0x20:-4])
  y[0x82:0x84] = struct.pack("<H", 27)
  y[0x10A:0x10C] = struct.pack("<H", 0)
  y[0x87] = 4
  y[0x10F] = 0
  y[0x1A6:0x1B2] = "Drawbar".ljust(12, " ").encode("ascii")

  upload_ac7_internal(DEST-801, bytes(y), memory=1, category=3)




if sys.platform.startswith('linux') and not sys.stdout.isatty():
  # Stdout is a linux pipe. Write the output to it.
  for SYX in sysex:
    sys.stdout.buffer.write(SYX)
else:
  # Save to a file
  with open("88800000.syx", "wb") as f1:
    for SYX in sysex:
      f1.write(SYX)

