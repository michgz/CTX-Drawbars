'''
Functions for making a custom drawbar organ instrument for the CT-X3000/5000
'''

import os
import os.path
import struct
import textwrap
import sys




# Internal function, returning the number of bytes of data for a certain parameter
def get_length_of_parameter(param, category=10):
  if category!=10:
    raise Exception("Only supports category 10")
  if param < 0 or param > 34:
    raise Exception(f"Invalid parameter number for category 10: {param}")
  if param in [0,4,20,27,32]:
    return 2
  else:
    return 1

# Internal function, make a SYSEX message to set a single parameter in the CT-X

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



'''
function: drawbar_sysex
brief:  Takes a list of split values, and returns a list of SYSEX messages to set up a VERSATILE
instrument with those splits
'''
def drawbar_sysex(SPLITS, params={}):
  
  
  sysex=[]




  TEST_SPLITS = [
        0x19A,   # ride cymbal
        70,      # marimba
        1013,    # bass gtr
        1017     # organ wheel
   ]



  def get_param_value(p):
    # If value is explicitly given in "params" dictionary use that, other return
    #  a default
    if params.get(p, None) is not None:
      return params.get(p)
      
    if p >= 0 and p<=3:
      return [0x58,0,0,0x7F][p-0]
    elif p>= 16 and p<=34:
      return [0,0x40,0,0,0x80,0x48,0x48,0,0x40,0,0,0x80,0x40,0x40,0,0,0x80,0x40,0x40][p-16]
    
    print(p)
    raise Exception



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
  sysex.append(set_single_parameter_as_syx(0, get_param_value(0)))   # overall volume
  sysex.append(set_single_parameter_as_syx(1, get_param_value(1)))
  sysex.append(set_single_parameter_as_syx(2, get_param_value(2)))
  sysex.append(set_single_parameter_as_syx(3, get_param_value(3)))
  for i in range(24):
    splt = 0 # "Empty" value
    if i < len(SPLITS):
      splt = SPLITS[i]
      
      
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
    sysex.append(set_single_parameter_as_syx(9, 0x02 if i == len(SPLITS)-1 else 0x02, block0=i))
    sysex.append(set_single_parameter_as_syx(10, 1 if (q & 0x40)!=0 else 0, block0=i))
    sysex.append(set_single_parameter_as_syx(11, 1 if (q & 0x20)!=0 else 0, block0=i))
    sysex.append(set_single_parameter_as_syx(12, 1 if (q & 0x10)!=0 else 0, block0=i))
    sysex.append(set_single_parameter_as_syx(13, 1 if (q & 0x08)!=0 else 0, block0=i))
    sysex.append(set_single_parameter_as_syx(14, 1 if (q & 0x04)!=0 else 0, block0=i))
    sysex.append(set_single_parameter_as_syx(15, (q & 0x03), block0=i))
    
  sysex.append(set_single_parameter_as_syx(16, get_param_value(16)))
  sysex.append(set_single_parameter_as_syx(17, get_param_value(17)))
  sysex.append(set_single_parameter_as_syx(18, get_param_value(18)))
  sysex.append(set_single_parameter_as_syx(19, get_param_value(19)))
  sysex.append(set_single_parameter_as_syx(20, get_param_value(20)))
  sysex.append(set_single_parameter_as_syx(21, get_param_value(21)))
  sysex.append(set_single_parameter_as_syx(22, get_param_value(22)))
  sysex.append(set_single_parameter_as_syx(23, get_param_value(23)))
  sysex.append(set_single_parameter_as_syx(24, get_param_value(24)))
  sysex.append(set_single_parameter_as_syx(25, get_param_value(25)))
  sysex.append(set_single_parameter_as_syx(26, get_param_value(26)))
  sysex.append(set_single_parameter_as_syx(27, get_param_value(27)))
  sysex.append(set_single_parameter_as_syx(28, get_param_value(28)))
  sysex.append(set_single_parameter_as_syx(29, get_param_value(29)))
  sysex.append(set_single_parameter_as_syx(30, get_param_value(30)))
  sysex.append(set_single_parameter_as_syx(31, get_param_value(31)))
  sysex.append(set_single_parameter_as_syx(32, get_param_value(32)))
  sysex.append(set_single_parameter_as_syx(33, get_param_value(33)))
  sysex.append(set_single_parameter_as_syx(34, get_param_value(34)))

  return sysex



'''
function: upload_sysex
brief:   Uploads a list of sysex messages to a port. Linux only
'''
def upload_sysex(sysex, dev_name="/dev/midi1"):

  f_midi = os.open(dev_name, os.O_RDWR)

  for SYX in sysex:
    os.write(f_midi, SYX)


  os.close(f_midi)


'''
function:  experimental_tone
brief:  Returns a tone file which can access a Versatile instrument
        as set up by the functions above
'''
def experimental_tone():

  # Set up Category 3. Start with preset data 089 ("CLICK ORGAN")
  #
  with open(os.path.join(os.path.dirname(__file__), "..", "internal", "Data", "089CLICKORG.TON"), "rb") as f2:
    y = bytearray(f2.read()[0x20:-4])
  y[0x82:0x84] = struct.pack("<H", 30)
  y[0x10A:0x10C] = struct.pack("<H", 0)
  y[0x87] = 6
  y[0x10F] = 0
  y[0x1A6:0x1B2] = "Drawbar".ljust(12, " ").encode("ascii")
  
  return bytes(y)




if __name__ == "__main__":
  
  
  # Calculate the SYSEX messages
  sysexs = drawbar_sysex([
              0x19A,   # ride cymbal
              70,      # marimba
              1013,    # bass gtr
              1017     # organ wheel
            ])
  
  
  # Send the SYSEX messages
  upload_sysex(sysexs)
  

  # The user tone number to write the experimental data into. 801-900
  #
  DEST = 801


  if False:
    write_experimental_tone(DEST)



  # Output somehow -- either to the output pipe, or to a file
  #
  if sys.platform.startswith('linux') and not sys.stdout.isatty():
    # Stdout is a linux pipe. Write the output to it.
    for SYX in sysexs:
      sys.stdout.buffer.write(SYX)
  else:
    # Save to a file
    with open("88800000.syx", "wb") as f1:
      for SYX in sysexs:
        f1.write(SYX)







