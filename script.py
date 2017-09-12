from mydy import Events, FileIO, Containers
from functools import reduce

TWELVE_ROOT_TWO = 2 ** (1 / 12)
Q_NOTE_PHRASE_LEN = 16  # number of times to repeat phrase per quarter note

# TODO: handle legato


def get_root(track):
    '''Gets the pitch of the first NoteOn event in a track'''
    for event in track:
        if isinstance(event, Events.NoteOnEvent):
            return event.pitch


def get_ratio(root, pitch):
    '''Calculate the ratio between two pitches'''
    # difference in semitones
    difference = pitch - root
    return TWELVE_ROOT_TWO ** (difference)


def get_note_info(track):
    '''
    Parse (note, length, tick) tuples from a track and return them in a List
    '''
    track.relative = True
    notes = []
    tracking = 0  # keep track of elapsed ticks, assume relative
    for i, event in enumerate(track):
        tracking += event.tick
        # NoteOn events sometimes happen before the previous note's off event,
        # so filter for that situation.
        if isinstance(event, Events.NoteOnEvent):
            if i == 0 or (isinstance(track[i - 1], Events.NoteOffEvent)):
                tick = event.tick
            else:
                tick = 0
            duration = find_note_off(tracking, event.pitch, i, track)
            notes.append((event.pitch, duration, tick))
    return notes


def find_note_off(start, pitch, i, track):
    '''
    Given the absolute starting tick and the pitch of a NoteOn event that
    happens at index i within a track, find its corresponding NoteOff event.
    Return the duration of the note as a tick value. Assumes relative tick.
    '''
    elapsed = 0
    # slicing creates a copy, but this is awkward
    for j in range(i + 1, len(track)):
        event = track[j]
        elapsed += event.tick
        # TODO: support NoteOn velocity = 0
        if isinstance(event, Events.NoteOffEvent) and event.pitch == pitch:
            return elapsed
    # if none is found, assume it should end at the end of the track length.
    return track.length - start


def fractalize_note(resolution, ratio_fn, track, note_info):
    '''
    Given a (note, duration, tick) tuple representing a note within the supplied
    track, return a repeated and timestretched version of the track
    representing a fractal version of the note.
    Params:
        resolution: number - resolution of the track
        ratio_fn: function - function to calculate the relative frequency of the
            note we are fractalizing with regard to the root of a track
        track: mydy.Track - the track we are fractalizing
        note_info: (number, number, number) - tuple of (pitch, duration, tick)
            information, e.g. (60, 96), would be "middle c for 96 ticks"
    Returns a new mydy.Track object
    '''
    pitch, duration, tick = note_info
    print(tick)
    quarter_notes = duration / resolution
    ratio = ratio_fn(pitch)
    qn_len = Q_NOTE_PHRASE_LEN * quarter_notes * ratio
    fract = (track / ratio) ** qn_len
    fract[0].tick = tick / resolution * track.length * Q_NOTE_PHRASE_LEN
    return fract


def fractalize_track(resolution, track):
    root = get_root(track)
    note_info = get_note_info(track)
    header, track = split_header_meta_events(track)
    endevent = None
    if isinstance(track[-1], Events.EndOfTrackEvent):
        endevent = track[-1]
        track = track[:-1]

    def ratio_wrt_root(pitch): return get_ratio(root, pitch)

    def f_note(note_info): return fractalize_note(resolution, ratio_wrt_root,
                                                  track, note_info)

    fractal = reduce(lambda x, y: x + y,
                     (f_note(note) for note in note_info))
    if endevent is not None:
        fractal.append(endevent)
    # print(fractal.filter(lambda e: isinstance(e, Events.NoteOnEvent)))
    return header + fractal


def split_header_meta_events(track):
    '''
    Split out the header MetaEvents from a track and return two tracks
    containing the header events and the body of the track.
    '''
    for i, event in enumerate(track):
        if not isinstance(event, Events.MetaEvent):
            return track[:i], track[i:]
    return Track(relative=track.relative), track


if __name__ == '__main__':
    sotw = FileIO.read_midifile('sotw2.mid')
    sotw_track = sotw[0]
    print(sotw_track)

    fractal = fractalize_track(sotw.resolution, sotw_track)

    fractal_pattern = Containers.Pattern(fmt=0, tracks=[fractal])
    fractal_pattern.resolution = 2 ** 15 - 1

    FileIO.write_midifile('test2.mid', Containers.Pattern(
        resolution=sotw.resolution * 1, fmt=sotw.format, tracks=[fractal]))
    # a = FileIO.read_midifile('test2.mid')
