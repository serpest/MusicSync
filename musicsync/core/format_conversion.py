import warnings

# pydub raises a warning during import if it couldn't find ffmpeg or avconv (programs used to convert
# audio files to another format), the following lines set ffmpeg__and_avconv_not_found_flag to True in that case
# without raising warning or exceptions not to have to handle them in the import format_conversion statement in
# other modules. In this way, the other modules have to handle this exception only if pydub is effectively used.
ffmpeg__and_avconv_not_found_flag = False
with warnings.catch_warnings(record=True) as w:
    warnings.filterwarnings(action="always", message="Couldn't find ffmpeg or avconv", category=RuntimeWarning)
    import pydub
    if len(w) > 0:
        ffmpeg__and_avconv_not_found_flag = True

def _raise_exception_if_converter_does_not_work():
    if ffmpeg__and_avconv_not_found_flag:
        raise FormatConverterNotFound("Couldn't find ffmpeg or avconv.")

def get_convert_song_function(input_filename, format, bitrate=None):
    return lambda output_filename : convert_song(input_filename, output_filename, format, bitrate)

def convert_song(input_filename, output_filename, format, bitrate=None):
    _raise_exception_if_converter_does_not_work()
    song = pydub.AudioSegment.from_file(input_filename)
    try:
        song.export(output_filename, format=format, bitrate=bitrate, tags=pydub.utils.mediainfo(input_filename).get("TAG", {})) # See https://github.com/jiaaro/pydub/issues/44
    except pydub.exceptions.CouldntEncodeError:
        raise FormatConvertersionError("Output file encording failed.")


class FormatConverterNotFound(RuntimeError):
    pass


class FormatConvertersionError(RuntimeError):
    pass
