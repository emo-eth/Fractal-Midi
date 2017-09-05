from mydy import Events, FileIO, Containers
from functools import reduce

TWELVE_ROOT_TWO = 2 ** (1 / 12)
mary = FileIO.read_midifile('sotw.mid')

def extend_relative(track, factor):
    # compute the length of the track in ticks
    length = reduce(lambda curr, event: curr + event.tick, track, 0)
    # grab the end-of-track-event
    end_of_track = track[-1]
    # grab everything but the end-of-track-event
    # this is the track we will be adding onto our returned track
    body = Containers.Track(events=filter(lambda x: not Events.MetaEvent.is_event(x.status), track[:-1]))
    # this will contain our new track
    new = track[:-1]
    # add body of event for whole
    for i in range(int(factor)):
        new += body
    # decide if we're extending by a float factor and add fractional bit on the end
    cutoff = length * (factor % 1)
    if cutoff:
        # keep track of absolute tick position and which notes are on
        pos = 0
        on = set()
        for i, event in enumerate(track):
            pos += event.tick
            if isinstance(event, Events.NoteOnEvent):
                on.add(event.pitch)
            elif isinstance(event, Events.NoteOffEvent):
                try:
                    on.remove(event.pitch)
                except KeyError:
                    pass
            if pos > cutoff:
                new += body[:i]
                for note in on:
                    tick = cutoff - (pos - event.tick)
                    track.append(Events.NoteOffEvent(tick=tick, pitch=note, velocity=0))
                break
    new.append(end_of_track)
    return new

def get_root(pattern):
    for track in pattern:
        for event in track:
            if isinstance(event, Events.NoteOnEvent):
                return event.pitch

def get_ratio(root, pitch):
    difference = pitch - root
    # sign = difference > 0
    # # account for weird modulo behavior of floor div
    # if sign:
    #     octave = (pitch - root) // 12
    # else:
    #     octave = (pitch - root) // 12 + 1
    # if octave:
    #     root *= 2 ** (sign * octave)
    return TWELVE_ROOT_TWO ** (difference)


root = get_root(mary)
print(get_ratio(root, 72 + 36))

FileIO.write_midifile('test2.mid', Containers.Pattern(resolution=mary.resolution, fmt=mary.format, tracks=[mary[0] ** 4.2]))
a = FileIO.read_midifile('test2.mid')
