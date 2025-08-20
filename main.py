from PIL import Image
import os, sys, subprocess, binascii
from shutil import rmtree

def bits_2_file(bits, fname):
    with open(fname, 'wb') as f:
        for i in range(0, len(bits), 8):
            byte = ''.join(bits[i:i+8])
            f.write(int(byte, 2).to_bytes(1, 'big'))
    print(f"Wrote {len(bits)} bits to {fname}")

def file_2_bits(fname):
    bits = []
    with open(fname, "rb") as f:
        byte = f.read(1)
        while byte:
            cur_bits = bin(byte[0])[2:].zfill(8)
            bits.extend(list(cur_bits))
            byte = f.read(1)
    return bits


def bits_2_pixels(bits):
    pixels = [(0,0,0) if b=='0' else (255,255,255) for b in bits]
    print("bits_2_pixels: Converted %d bits to %d pixels" % (len(bits),len(pixels)))
    return pixels 

def pixels_2_bits(pixels):
    bits = ['0' if p==(0,0,0) else '1' for p in pixels]
    print("pixels_2_bits: Converted %d pixels to %d bits" % (len(pixels),len(bits)))
    return bits


def pixels_2_png(pixels, fname, res=(512,512)):
    img = Image.new('RGB', res)
    img.putdata(pixels[:res[0]*res[1]])
    img.save(fname)
    print(f"Saved {fname}")

def png_2_pixels(fname):
    im = Image.open(fname)
    pixels = list(im.getdata())
    print(f"Read {len(pixels)} pixels from {fname}")
    return pixels

import binascii

def add_header(bits, fname):
    fname_bits = bin(int(binascii.hexlify(fname.encode()),16))[2:]
    fname_len = bin(len(fname_bits))[2:].zfill(16)
    payload_len = bin(len(bits))[2:].zfill(64)
    return list(fname_len + fname_bits + payload_len) + bits

def decode_header(bits):
    fname_len = int(''.join(bits[:16]),2)
    fname_bits = ''.join(bits[16:16+fname_len])
    fname = binascii.unhexlify('%x' % int(fname_bits,2)).decode()
    payload_len = int(''.join(bits[16+fname_len:16+fname_len+64]),2)
    return fname, bits[16+fname_len+64:16+fname_len+64+payload_len]

def main():
    orig_bits = file_2_bits("data/test.zip")
    wrapped = add_header(orig_bits, "test.zip")
    fname, payload = decode_header(wrapped)
    print("Decoded fname:", fname)
    print("Payload bits:", len(payload))

