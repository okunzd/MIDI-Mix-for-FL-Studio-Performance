# name=MIDIMix

import time
import midi
import device

# ——— CONFIG ———
NOTE_MIN = 1
NOTE_MAX = 26
REFRESH_INTERVAL = 0.5  # seconds between resyncs
# default-on toggle notes: D#0=3, F#0=6, A0=9, C1=12, D#1=15, F#1=18, A1=21, C2=24
DEFAULT_ON = {3, 6, 9, 12, 15, 18, 21, 24}

# internal state
buttonStates = {}    # notes 1–25 toggles
note26Held = False   # momentary
note26Chan = 0       # remember channel for note 26
lastRefresh = 0.0

def lightOn(note, chan):
    device.midiOutMsg(144, chan, note, 127)

def lightOff(note, chan):
    device.midiOutMsg(144, chan, note, 0)

def OnInit():
    global lastRefresh, note26Held
    lastRefresh = time.time()
    note26Held = False
    # initialize all notes
    for n in range(NOTE_MIN, NOTE_MAX + 1):
        # notes 1–25: default toggle state
        if n in DEFAULT_ON and n != 26:
            buttonStates[n] = True
            lightOn(n, 0)
        else:
            buttonStates[n] = False
            lightOff(n, 0)

def OnIdle():
    global lastRefresh
    now = time.time()
    if now - lastRefresh < REFRESH_INTERVAL:
        return
    # resync all toggle LEDs
    for n in range(NOTE_MIN, NOTE_MAX + 1):
        if n == 26:
            # momentary always off unless held
            continue
        if buttonStates.get(n, False):
            lightOn(n, 0)
        else:
            lightOff(n, 0)
    # resync note 26
    if note26Held:
        lightOn(26, note26Chan)
    else:
        lightOff(26, note26Chan)
    lastRefresh = now

def OnMidiMsg(event):
    global note26Held, note26Chan

    status = event.midiId    # 144 = Note On, 128 = Note Off
    chan   = event.midiChan  # 0–15
    note   = event.data1
    vel    = event.data2

    # only respond to notes 1–26
    if note < NOTE_MIN or note > NOTE_MAX or status not in (144, 128):
        event.handled = False
        return

    # Note 26: momentary
    if note == 26:
        if status == 144 and vel > 0:
            note26Held = True
            note26Chan = chan
            lightOn(26, chan)
        else:
            note26Held = False
            lightOff(26, chan)
        event.handled = False
        return

    # Notes 1–25: toggle on press only
    if 1 <= note <= 25 and status == 144 and vel > 0:
        buttonStates[note] = not buttonStates[note]
        if buttonStates[note]:
            lightOn(note, chan)
        else:
            lightOff(note, chan)
        event.handled = False
        return

    event.handled = False
