# -*- coding: utf-8 -*- 

import os
import xbmc, xbmcvfs, xbmcgui
from struct import Struct
import urllib

from StringIO import StringIO
import gzip

def log(module, msg):
    xbmc.log((u"### [%s] - %s" % (module, msg)).encode('utf-8'), level=xbmc.LOGDEBUG)

def get_file_size(filename, is_rar):
    try:
        if is_rar:
            file_size = get_file_size_from_rar(filename)
            return -1 if file_size == None else file_size
        else:
            return xbmcvfs.Stat(filename).st_size()
    except:
        return -1

# Based on https://github.com/markokr/rarfile/blob/master/rarfile.py
def get_file_size_from_rar(first_rar_filename):

    log_name = __name__ + " [RAR]"

    RAR_BLOCK_MAIN          = 0x73 # s
    RAR_BLOCK_FILE          = 0x74 # t
    RAR_FILE_LARGE          = 0x0100
    RAR_ID = str("Rar!\x1a\x07\x00")

    S_BLK_HDR = Struct('<HBHH')
    S_FILE_HDR = Struct('<LLBLLBBHL')
    S_LONG = Struct('<L')

    fd = xbmcvfs.File(first_rar_filename)
    if fd.read(len(RAR_ID)) == RAR_ID:
        log(log_name, "Reading file headers")
        while True:

            buf = fd.read(S_BLK_HDR.size)
            if not buf: return None

            t = S_BLK_HDR.unpack_from(buf)
            header_crc, header_type, header_flags, header_size = t
            pos = S_BLK_HDR.size

            # read full header
            header_data = buf + fd.read(header_size - S_BLK_HDR.size) if header_size > S_BLK_HDR.size else buf

            if len(header_data) != header_size: return None # unexpected EOF?

            if header_type == RAR_BLOCK_MAIN:
                log(log_name, "Main block found")
                continue
            elif header_type == RAR_BLOCK_FILE:
                log(log_name, "File block found")
                file_size = S_FILE_HDR.unpack_from(header_data, pos)[1]
                log(log_name, "File in rar size: %s" % file_size)
                if header_flags & RAR_FILE_LARGE: # Large file support
                    log(log_name, "Large file flag")
                    file_size |= S_LONG.unpack_from(header_data, pos + S_FILE_HDR.size + 4)[0] << 32
                    log(log_name, "File in rar size: %s after large file" % file_size)
                return file_size
            else:
                log(__name__, "RAR unknown header type %s" % header_type)
                return None
    else:
        return None


def extract_subtitles(archive_dir):
    xbmc.executebuiltin(('XBMC.Extract("%s")' % archive_dir).encode('utf-8'))
    xbmc.sleep(1000)
    basepath = os.path.dirname(archive_dir)
    extracted_files = os.listdir(basepath)
    exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
    extracted_subtitles = []
    if len(extracted_files) < 1 :
      return []
    else:
      for extracted_file in extracted_files:
        if os.path.splitext(extracted_file)[1] in exts:
          extracted_subtitles.append(os.path.join(basepath, extracted_file))
    return extracted_subtitles

def get_content_from_response(response):
    content = response.read()
    response.close()

    if response.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(content)
        f = gzip.GzipFile(fileobj=buf)
        content = f.read()

    return content
