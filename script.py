from mydy import Events, FileIO, Containers
from functools import reduce

TWELVE_ROOT_TWO = 2 ** (1 / 12)
Q_NOTE_PHRASE_LEN = 16  # number of times to repeat phrase per quarter note


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
    '''Parse (note, length) tuples from a track and return them in a List'''
    notes = []
    tracking = 0  # keep track of elapsed ticks, assume relative
    for i, event in enumerate(track):
        tracking += event.tick
        if isinstance(event, Events.NoteOnEvent):
            duration = find_note_off(tracking, event.pitch, i, track)
            notes.append((event.pitch, duration))
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
    Given a (note, duration) tuple representing a note within the supplied
    track, return a repeated and timestretched version of the track
    representing a fractal version of the note.
    Params:
        resolution: number - resolution of the track
        ratio_fn: function - function to calculate the relative frequency of the
            note we are fractalizing with regard to the root of a track
        track: mydy.Track - the track we are fractalizing
        note_info: (number, number) - tuple of (pitch, duration) information.
            eg (60, 96), would be "middle c for 96 ticks"
    Returns a new mydy.Track object
    '''
    pitch, duration = note_info
    quarter_notes = duration / resolution
    ratio = ratio_fn(pitch)
    qn_len = Q_NOTE_PHRASE_LEN * quarter_notes * ratio
    fract = (track / ratio) ** qn_len
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
    sotw = FileIO.read_midifile('sotw.mid')
    sotw_track = sotw[0]

    # root = get_root(sotw_track)
    # notes = get_note_info(sotw_track)

    # # curry helper functions
    # def ratio_wrt_root(pitch): return get_ratio(root, pitch)

    # def fractalize_sotw_note(note_info): return fractalize_note(
    #     sotw.resolution, ratio_wrt_root, sotw_track[3:-1], note_info)

    # # sanity check
    # assert(len(fractalize_sotw_note([60, sotw.resolution * 2])) ==
    #     (len(sotw_track[3:-1])) * Q_NOTE_PHRASE_LEN * 2), "Incorrect length"

    # fractal = reduce(lambda x, y: x + y, (fractalize_sotw_note(ni).filter(
    #     lambda e: not isinstance(e, Events.EndOfTrackEvent)) for ni in notes))
    fractal = fractalize_track(sotw.resolution, sotw_track)
    # header = sotw_track[:3]
    # header, sotw_track = split_header_meta_events(sotw_track)
    # endevent = sotw_track[-1]
    # fractal = header + fractal + Containers.Track([endevent])
    fractalP = Containers.Pattern(fmt=0, tracks=[fractal])
    fractalP.resolution = 2 ** 15 - 1
    # just_root_30 = fractal.filter(lambda e: isinstance(
    #     e, Events.NoteEvent) and e.pitch)  # == 60)
    # print(fractalP.resolution, list(sorted(filter(lambda x: x > 1, map(lambda e: e.tick / sotw.resolution, just_root_30)))))

    FileIO.write_midifile('test2.mid', Containers.Pattern(
        resolution=sotw.resolution * 1, fmt=sotw.format, tracks=[fractal]))
    a = FileIO.read_midifile('test2.mid')
    # a.relative = False
    a.resolution = 100
    print(a)
    print('~~~')
    just_root = a[0].filter(lambda e: isinstance(
        e, Events.NoteEvent) and e.pitch == 60)
    # print(just_root)
    # ticks = []
    # for i, e in enumerate(just_root):
    #     if i:
    #         ticks.append(e.tick - just_root[i-1].tick)
    # print(sorted(list(map(lambda t: t / a.resolution, ticks))))
    # print(fractalP.resolution, list(sorted(filter(lambda x: x > 1, map(lambda e: e.tick / a.resolution, a[0])))))
    # print(list(filter(lambda t: t[0] == 60, map(lambda t: (t[0], t[1] / a.resolution), get_note_info(a[0])))))
