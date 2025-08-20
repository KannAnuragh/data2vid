from __future__ import print_function

from PIL import Image
import binascii
import os, sys, subprocess
from shutil import rmtree

four_k = (3840,2160)
HD = (1920,1080)

# ===============================
# File <-> Bits
# ===============================

def bits_2_file(bits,fname):
    f = open(fname,'wb')
    idx=0
    inc=8
    while True:
        char = ''.join(bits[idx:idx+inc])
        f.write(chr(int(char,2)).encode("latin1"))
        idx+=inc
        if idx>=len(bits): break
    f.close()
    print("bits_2_file: Wrote %d bits to %s" % (len(bits),fname))

def file_2_bits(fname):
    bits = []
    f = open(fname, "rb")
    try:
        byte = f.read(1)
        while byte != b"":
            cur_bits = bin(ord(byte))[2:] if isinstance(byte,str) else bin(byte[0])[2:]
            while len(cur_bits)<8:
                cur_bits = "0"+cur_bits
            bits.extend(list(cur_bits))
            byte = f.read(1)
    finally:
        f.close()
    return bits

# ===============================
# Bits <-> Pixels
# ===============================

def bits_2_pixels(bits):
    pixels = [(0,0,0) if b=='0' else (255,255,255) for b in bits]
    print("bits_2_pixels: Converted %d bits to %d pixels" % (len(bits),len(pixels)))
    return pixels 

def pixels_2_bits(pixels):
    bits = ['0' if p==(0,0,0) else '1' for p in pixels]
    print("pixels_2_bits: Converted %d pixels to %d bits" % (len(pixels),len(bits)))
    return bits

# ===============================
# Image <-> Pixels
# ===============================

def pixels_2_png(pixels,fname,reso=four_k):
    img = Image.new('RGB',reso)
    img.putdata(pixels)
    img.save(fname)
    print("pixels_2_png: Saved %d pixels to %s" % (len(pixels),fname))

def png_2_pixels(fname):
    im = Image.open(fname)
    pixel_list = []
    pixels = im.load()
    width,height = im.size
    for row in range(height):
        for col in range(width):
            pixel_list.append(pixels[col,row])
    print("png_2_pixels: Read %d pixels from %s" % (len(pixel_list),fname))
    return pixel_list

# ===============================
# Headers
# ===============================

def add_header(bits,fname):
    # filename as binary
    fname_bitstr = bin(int(binascii.hexlify(fname.encode()), 16))
    fname_bitstr_length_bitstr = "{0:b}".format(len(fname_bitstr)-2)
    while len(fname_bitstr_length_bitstr)<16:
        fname_bitstr_length_bitstr = "0"+fname_bitstr_length_bitstr
    fname_headers = fname_bitstr_length_bitstr+fname_bitstr[2:]

    # filename header
    header_list = list(fname_headers)

    # payload size header (64 bits)
    payload_length_header = "{0:b}".format(len(bits))
    while len(payload_length_header)<64:
        payload_length_header = "0"+payload_length_header
    header_list.extend(list(payload_length_header))

    # append bits
    header_list.extend(bits)
    return header_list

def decode_header(bits):

    def decode_binary_string(s):
        return ''.join(chr(int(s[i*8:i*8+8],2)) for i in range(len(s)//8))

    fname_length_binstr = ''.join(bits[:16])
    fname_length = int(fname_length_binstr,2)
    print("decode_header: fname_length: %d" % fname_length)

    fname_binstr = ''.join(bits[16:16+fname_length])
    fname_binstr = "0"+fname_binstr
    fname = decode_binary_string(fname_binstr)
    print("decode_header: fname: %s"%fname)

    payload_length_binstr = ''.join(bits[16+fname_length:16+fname_length+64])
    payload_length = int(payload_length_binstr,2)
    print("decode_header: payload_length: %d" % payload_length)

    return fname,bits[16+fname_length+64:16+fname_length+64+payload_length]

# ===============================
# Utilities
# ===============================

def clear_folder(relative_path):
    try:
        rmtree(relative_path)
    except:
        print ("WARNING: Could not locate directory.")
    for i in range(10):
        try:
            os.mkdir(relative_path)
            break
        except:
            continue

# ===============================
# FFV1 Video Creation
# ===============================

def make_ffv1(parent_folder, fname):
    out_name = fname + ".mkv"
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "1",
        "-i", os.path.join(parent_folder, fname + "-%d.png"),
        "-c:v", "ffv1",
        out_name
    ]
    subprocess.run(cmd, check=True)
    return out_name

# ===============================
# Encode / Decode
# ===============================

def encode(src,res=four_k):
    bits  = file_2_bits(src)
    bits  = add_header(bits,src.split("/")[-1])
    pixels = bits_2_pixels(bits)

    pixels_per_image = res[0]*res[1]
    num_imgs = int(len(pixels)/pixels_per_image)+1
    print ("encode: Encoding will require %d .png frames" % num_imgs)

    name_clean = src.split("/")[-1]
    clear_folder("temp")

    for i in range(num_imgs):
        cur_temp_name = "temp/"+name_clean+"-%d.png" % i
        cur_start_idx = i*pixels_per_image
        cur_span = min(pixels_per_image, len(pixels)-cur_start_idx)
        cur_pixels = pixels[cur_start_idx:cur_start_idx+cur_span]
        pixels_2_png(cur_pixels,cur_temp_name,res)
        if cur_span<pixels_per_image: break

    ffv1_name = make_ffv1("temp", name_clean)
    return ffv1_name

def decode(src):
    clear_folder("temp")
    subprocess.run(["ffmpeg", "-i", src, "temp/frame-%d.png"], check=True)

    saved_frames = sorted([f for f in os.listdir("temp") if f.endswith(".png")])
    print("decode: Identified %d .png frames" % len(saved_frames))

    pixels = []
    for s in saved_frames:
        cur_pixels = png_2_pixels("temp/"+s)
        pixels.extend(cur_pixels)

    bits = pixels_2_bits(pixels)
    fname,bits = decode_header(bits)
    outname = fname.split(".")[0]+"-recovered."+fname.split(".")[1]
    bits_2_file(bits, outname)

# ===============================
# Main
# ===============================

def main():
    encode("data/test.zip")
    decode("test.zip.mkv")

if __name__ == '__main__':
    main()
