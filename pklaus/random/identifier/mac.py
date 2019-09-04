
"""
https://gist.github.com/pklaus/9638536
https://en.wikipedia.org/wiki/MAC_address#Universal_vs._local
"""

import random

def random_bytes(num=6):
    return [random.randrange(256) for _ in range(num)]

def generate_mac(uaa=False, multicast=False, oui=None, separator=':', byte_fmt='%02x'):
    mac = random_bytes()
    if oui:
        if type(oui) == str:
            oui = [int(chunk) for chunk in oui.split(separator)]
        mac = oui + random_bytes(num=6-len(oui))
    else:
        if multicast:
            mac[0] |= 1 # set bit 0
        else:
            mac[0] &= ~1 # clear bit 0
        if uaa:
            mac[0] &= ~(1 << 1) # clear bit 1
        else:
            mac[0] |= 1 << 1 # set bit 1
    return separator.join(byte_fmt % b for b in mac)

def generate_macs(number, **kwargs):
    entropy_bits = 6*8-2
    oui, separator = kwargs.get('oui', None), kwargs.get('separator', ':')
    if oui:
        entropy_bits = (6 - len(oui.split(separator)))*8
    if number > 2**entropy_bits:
        raise ValueError(f"Impossible to sample more than {2**entropy_bits} addresses")
    elif number > 0.5 * 2**entropy_bits:
        import sys
        print(f"Warning: Asked to sample {number} MACs out of an address space of {2**entropy_bits}. "
              f"The implementation is not suited for this ratio and will be slow.", file=sys.stderr)
    macs = set()
    while len(macs) < number:
        mac = generate_mac(**kwargs)
        if mac in macs:
            continue
        macs.add(generate_mac(**kwargs))
        yield mac

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--number', type=int, default=1, help='Number of MACs to generate.')
    parser.add_argument('--uaa', action='store_true', help='generates a universally administered address (instead of LAA otherwise)')
    parser.add_argument('--multicast', action='store_true', help='generates a multicast MAC (instead of unicast otherwise)')
    parser.add_argument('--oui', help='enforces a specific organizationally unique identifier (like 00:60:2f for Cisco)')
    parser.add_argument('--byte-fmt', default='%02x', help='The byte format. Set to %02X for uppercase hex formatting.')
    parser.add_argument('--separator', default=':', help="The byte separator character. Defaults to ':'.")
    args = parser.parse_args()
    kwargs = dict(oui=args.oui, uaa=args.uaa, multicast=args.multicast, separator=args.separator, byte_fmt=args.byte_fmt)
    for mac in generate_macs(args.number, **kwargs):
        print(mac)
