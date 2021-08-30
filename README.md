# CTX-Drawbars
User-defined Drawbar Organ sounds on the Casio CT-X keyboard. Some pre-defined mix settings are available here, and others can be created with an included script that runs in Python.

Works on CT-X3000 and CT-X5000. Probably not on CT-X700/800.

## How to use

1. Copy the file DRAWBAR.TON to the user tone memory, either using a USB memory stick or the CT-X Data Manager application. If the later, remember to close the application to free up the MIDI port for step 3. below. This same tone is used for all tonewheel mixes.
2. Select the .syx file you wish to use. If none suit and you are willing to work with the Python programming language, you can create some of your own (see "Regenerating the files" below).
3. Send the .syx file to the keyboard. How to do this depends on the operating system that you are using:

- Linux:
Send directly using the `amidi` command. It's possible to find the name of the port with `amidi -l` - in the example below, it is "hw:1,0,0":
```
> amidi -l
Dir Device    Name
IO  hw:1,0,0  CASIO USB-MIDI MIDI 1
> amidi -p hw:1,0,0 --send=88800000.syx
```

- Windows:
Use any program that can send binary SYX files to a MIDI port, for example MIDI-Ox.

### Regenerating the files

All the .syx and .TON files are generated by a Python script in the `scripts` directory. If you want to create your own mix of tonewheels, this script can be edited and run.

In Windows:
```
python scripts\make_all.py
```

In Linux:
```
python scripts/make_all.py
```

Requires Python 3.
