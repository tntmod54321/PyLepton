import ctypes
import ctypes.util
import platform
import xxhash

match platform.system():
    case 'Windows':
        dllpath = ctypes.util.find_library('lepton_jpeg.dll')
    case 'Linux':
        from os import getcwd
        import os.path
        dllpath = ctypes.util.find_library('liblepton_jpeg.so') or \
                  os.path.join(getcwd(), 'liblepton_jpeg.so')
    case _:
        raise Exception(f'unimplemented support for platform {platform.system()}')

if not dllpath:
    raise Exception(f'unable to find lepton_jpeg/liblepton_jpeg library')

lepton = ctypes.CDLL(dllpath)

lepton.WrapperCompressImage.restype = ctypes.c_int32
lepton.WrapperDecompressImage.restype = ctypes.c_int32

def encode(jpeg: bytes, threads: int = 4) -> bytes:
    lepbuf = (ctypes.c_uint8 * len(jpeg))(0x00)
    lepbuflen = ctypes.c_uint64()
    
    rc = lepton.WrapperCompressImage(
        ctypes.byref((ctypes.c_ubyte * len(jpeg)).from_buffer_copy(jpeg)), # input buf ptr (from_buffer_copy doubles the indat mem usage)
        ctypes.c_uint64(len(jpeg)), # ilen
        ctypes.byref(lepbuf), # output buf ptr
        ctypes.c_uint64(len(jpeg)), #olen
        ctypes.c_int32(threads), # threads
        ctypes.byref(lepbuflen)) # out data len ptr
    
    if rc != 0:
        raise RuntimeError(f'lepton encode returned code {rc}')
    
    return bytes(lepbuf)[:lepbuflen.value]

def decode(lep: bytes, threads: int = 4) -> bytes:
    # very liberal alloc of mem for dec /shrug
    jpgbuflenmax = max(128000, len(lep) * 3)
    jpgbuf = (ctypes.c_uint8 * jpgbuflenmax)(0x00)
    jpgbuflen = ctypes.c_uint64()
    
    rc = lepton.WrapperDecompressImage(
        ctypes.byref((ctypes.c_ubyte * len(lep)).from_buffer_copy(lep)), # input buf ptr (from_buffer_copy doubles the indat mem usage)
        ctypes.c_uint64(len(lep)), # ilen
        ctypes.byref(jpgbuf), # output buf ptr
        jpgbuflenmax, # olen
        ctypes.c_int32(threads), # threads
        ctypes.byref(jpgbuflen)) # out data len ptr
    
    if rc != 0:
        raise RuntimeError(f'lepton decode returned code {rc}')
    
    return bytes(jpgbuf)[:jpgbuflen.value]

class VerifiedLep:
    def __init__(self, lep: bytes, jpeghash: xxhash.xxh3_128):
        self.data = lep
        self.jpeghash = jpeghash

def encode_verify(jpeg: bytes, threads: int = 4) -> VerifiedLep:
    lep = encode(jpeg, threads=threads)
    jpeg_tmp = decode(lep, threads=threads)
    
    srchash = xxhash.xxh3_128(jpeg)
    dechash = xxhash.xxh3_128(jpeg_tmp)
    if srchash.digest() != dechash.digest():
        raise RuntimeError('decoded file does not match source file!')
    
    return VerifiedLep(lep, srchash)

