import os

PAK_FILES = [
    "msedge_100_percent.pak",
    "msedge_200_percent.pak",
    "resources.pak",
]

# File signatures
PNG = b"\x89PNG\r\n\x1a\n"
WEBP = b"RIFF"
WEBP_TYPE = b"WEBP"

JPEG = b"\xff\xd8\xff"


def find_png_end(data, start):
    """Find the end of a PNG using its IEND chunk."""
    end_marker = data.find(b"IEND", start + 8)

    if end_marker < 0:
        return None

    # IEND is 4 bytes, followed by its 4-byte CRC
    return end_marker + 8


def find_webp_end(data, start):
    """Find the end of a WebP using the RIFF size field."""
    if start + 8 > len(data):
        return None

    # RIFF file size is stored as little-endian uint32 at offset +4.
    size = int.from_bytes(data[start + 4:start + 8], "little")

    # RIFF size does not include the first 8 bytes.
    end = start + 8 + size

    if end > len(data):
        return None

    return end


def find_jpeg_end(data, start):
    """Find the JPEG EOI marker."""
    end_marker = data.find(b"\xff\xd9", start + 3)

    if end_marker < 0:
        return None

    return end_marker + 2


for pak_file in PAK_FILES:
    output_folder = os.path.splitext(pak_file)[0]
    os.makedirs(output_folder, exist_ok=True)

    with open(pak_file, "rb") as f:
        d = f.read()

    print(f"\nProcessing {pak_file}...")

    # Find every supported image signature first.
    images = []

    # PNG
    p = 0
    while True:
        start = d.find(PNG, p)
        if start < 0:
            break

        end = find_png_end(d, start)

        if end is not None:
            images.append((start, end, ".png"))
            p = end
        else:
            print("Incomplete PNG at", start)
            p = start + 8

    # WebP
    p = 0
    while True:
        start = d.find(WEBP, p)
        if start < 0:
            break

        # Make sure this RIFF is actually a WebP.
        if d[start + 8:start + 12] == WEBP_TYPE:
            end = find_webp_end(d, start)

            if end is not None:
                images.append((start, end, ".webp"))
                p = end
            else:
                print("Incomplete WebP at", start)
                p = start + 4
        else:
            p = start + 4

    # JPEG
    p = 0
    while True:
        start = d.find(JPEG, p)
        if start < 0:
            break

        end = find_jpeg_end(d, start)

        if end is not None:
            images.append((start, end, ".jpg"))
            p = end
        else:
            print("Incomplete JPEG at", start)
            p = start + 3

    # Sort images by their location in the PAK.
    images.sort(key=lambda x: x[0])

    # Extract them using simple sequential numbering.
    n = 0

    for start, end, extension in images:
        n += 1
        filename = os.path.join(output_folder, f"{n}{extension}")

        with open(filename, "wb") as f:
            f.write(d[start:end])

        print(
            f"{n:3d}: "
            f"offset={start:8d} "
            f"size={end-start:7d} "
            f"{filename}"
        )

    print(f"Extracted {n} images from {pak_file}.")

print("\nDone.")