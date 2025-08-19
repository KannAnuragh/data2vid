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

def main():
    bits = file_2_bits("data/test.zip")
    pixels = bits_2_pixels(bits)
    pixels_2_png(pixels, "temp.png", (512,512))
    recovered = png_2_pixels("temp.png")
    back_bits = pixels_2_bits(recovered)
    print("Recovered bits length:", len(back_bits))

