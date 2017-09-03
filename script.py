from mydy import Events, FileIO
from functools import reduce

mary = FileIO.read_midifile('mary.mid')

def extend_relative(track, factor):
    length = reduce(lambda curr, event: curr + event.tick, track, 0)
    end_of_track = track[-1]
    body = track[:-1]
    new = body.copy()
    for i in range(int(factor)):
        new += body
    pos = 0
    on = set()
    for i, event in enumerate(track):
        pos += event.tick
        if isinstance(event, Events.NoteOnEvent):
            on.add(event.pitch)
        elif isinstance(event, Events.NoteOffEvent):
            on.remove(event.pitch)
        cutoff = length * (factor % 1)
        if pos > cutoff:
            new += body[:i]
            for note in on:
                tick = cutoff - (pos - event.tick)
                track.append(Events.NoteOffEvent(tick=tick, pitch=note, velocity=0))
            break
    new.append(end_of_track)
    return new
    # print(track)

print(extend_relative(mary[1] * 3 / 2, 36))
