import io
import pydub

def get_convert_and_copy_song_function(input_filename, format, bitrate=None):
    song = pydub.AudioSegment.from_file(input_filename)
    return lambda output_filename : song.export(output_filename, format=format, bitrate=bitrate)
