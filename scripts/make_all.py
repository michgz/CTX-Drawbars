'''
Script to make all the drawbar organ files.
'''

import os
import os.path
import struct
import binascii

import drawbar_organ



ORGAN_DEFINITIONS = [

  { 'name': '88800000', 'splits': [74] },


  #{ 'name': '88800004', 'splits': [74, 726] },
  
  
  { 'name': '08088000', 'splits': [1015] },


  { 'name': '08088060', 'splits': [1015, 1016] },
  # Sounds decent!
  
  
  { 'name': '88800004', 'splits': [1020, 726] },
  # Ok. Need to tame overload
  

  
]




# Wrap a tone parameter set to make it suitable for saving as a .TON file
#   (add CRCs, etc...)
def wrap_tone_file(x):

  y = b'CT-X3000'
  y += struct.pack('<2I', 0, 0)
  y += b'TONH'
  y += struct.pack('<3I', 0, binascii.crc32(x), len(x))
  y += x
  y += b'EODA'
  return y


if __name__ == "__main__":

  DEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
  
  print("Running a script to make all the drawbar organ files")
  
  print("  1. Creating DRAWBAR.TON")
  
  # Create the experimental tone, wrap it suitable for saving as a file, and
  #  save it.
  #
  # If it already exists, this will overwrite it.
  with open(os.path.join(DEST_DIR, "DRAWBAR.TON"), "wb") as f_ton:
    f_ton.write(wrap_tone_file(drawbar_organ.experimental_tone()))
    
  print("  2. Creating SYSEX files:")
  
  for ORGAN in ORGAN_DEFINITIONS:
    
    print("       {0}".format(ORGAN['name']))
    
    # Create the list of SYSEX messages, and deal with them as required.
    
    DO_SYX_BINARY = True  # MIDI-Ox style "binary" sysex format
    DO_SYX_TEXT = False   # MIDI-Ox style "text" sysex format. Set to "True" if needed
    # ....also need a standard MIDI format??
    
    
    syxes = drawbar_organ.drawbar_sysex(ORGAN['splits'])
    
    if DO_SYX_BINARY:
      with open(os.path.join(DEST_DIR, ORGAN['name'] + '.syx'), "wb") as f_syx:
        for SYX in syxes:
          f_syx.write(SYX)
    if DO_SYX_TEXT:
      with open(os.path.join(DEST_DIR, ORGAN['name'] + '_.syx'), "w") as f_syx:
        for SYX in syxes:
          f_syx.write(SYX.hex(" ") + "\n")

