"""Minimal RTON (PopCap) reader/writer for PvZ2 pp.dat.

Values decode to plain Python types, except ints keep their wire tag
(RInt) and RTIDs stay as RTID, so encode(decode(x)) round-trips.
"""
import struct


class RInt(int):
    def __new__(cls, v, tag=0x25):
        o = int.__new__(cls, v)
        o.tag = tag
        return o


class RTID(str):
    def __new__(cls, v, raw=b''):
        o = str.__new__(cls, v)
        o.raw = raw
        return o


class RStr(str):
    """String stored uncached (tag 0x81 latin1 / 0x82 utf8) in the source file."""
    def __new__(cls, v, tag=0x81):
        o = str.__new__(cls, v)
        o.tag = tag
        return o


class RFloat(float):
    def __new__(cls, v, tag=0x22):
        o = float.__new__(cls, v)
        o.tag = tag
        return o


def _rvar(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1
        r |= (c & 0x7f) << s; s += 7
        if c < 0x80:
            return r, i


def _wvar(n):
    out = bytearray()
    while True:
        c = n & 0x7f; n >>= 7
        if n:
            out.append(c | 0x80)
        else:
            out.append(c)
            return bytes(out)


_FIX = {0x08: 'b', 0x0a: 'B', 0x10: 'h', 0x12: 'H', 0x20: 'i', 0x26: 'I', 0x40: 'q', 0x46: 'Q'}
_ZERO = {0x09, 0x0b, 0x11, 0x13, 0x21, 0x27, 0x41, 0x47}


class _Reader:
    def __init__(self, b):
        self.b, self.i, self.sc, self.uc = b, 0, [], []

    def str_(self, t):
        b, i = self.b, self.i
        if t == 0x81:
            n, i = _rvar(b, i); s = RStr(b[i:i + n].decode('latin1')); i += n
        elif t in (0x82, 0x92):
            _, i = _rvar(b, i); n, i = _rvar(b, i); s = b[i:i + n].decode('utf-8'); i += n
            if t == 0x92: self.uc.append(s)
            else: s = RStr(s, 0x82)
        elif t == 0x90:
            n, i = _rvar(b, i); s = b[i:i + n].decode('latin1'); i += n; self.sc.append(s)
        elif t == 0x91:
            k, i = _rvar(b, i); s = self.sc[k]
        elif t == 0x93:
            k, i = _rvar(b, i); s = self.uc[k]
        else:
            raise ValueError(f'not a string tag {t:#x} at {self.i - 1}')
        self.i = i
        return s

    def val(self):
        b = self.b
        t = b[self.i]; self.i += 1
        if t in (0x00, 0x01): return bool(t)
        if t in _FIX:
            f = '<' + _FIX[t]; v = struct.unpack_from(f, b, self.i)[0]; self.i += struct.calcsize(f)
            return RInt(v, t)
        if t in _ZERO: return RInt(0, t)
        if t in (0x24, 0x28, 0x44, 0x48):
            v, self.i = _rvar(b, self.i); return RInt(v, t)
        if t in (0x25, 0x29, 0x45, 0x49):
            v, self.i = _rvar(b, self.i); return RInt((v >> 1) ^ -(v & 1), t)
        if t in (0x22, 0x42):
            f = '<f' if t == 0x22 else '<d'; v = struct.unpack_from(f, b, self.i)[0]
            self.i += 4 if t == 0x22 else 8; return RFloat(v, t)
        if t in (0x23, 0x43): return RFloat(0.0, t)
        if t in (0x81, 0x82, 0x90, 0x91, 0x92, 0x93): return self.str_(t)
        if t in (0x83, 0x84):
            start = self.i - 1
            if t == 0x83:
                sub = b[self.i]; self.i += 1
                if sub == 0x02:
                    _, self.i = _rvar(b, self.i); n, self.i = _rvar(b, self.i); s = b[self.i:self.i + n].decode(); self.i += n
                    a, self.i = _rvar(b, self.i); c, self.i = _rvar(b, self.i); u = struct.unpack_from('<I', b, self.i)[0]; self.i += 4
                    txt = f'RTID({c}.{a}.{u:08x}@{s})'
                elif sub == 0x03:
                    parts = []
                    for _ in range(2):
                        _, self.i = _rvar(b, self.i); n, self.i = _rvar(b, self.i); parts.append(b[self.i:self.i + n].decode()); self.i += n
                    txt = f'RTID({parts[1]}@{parts[0]})'
                elif sub == 0x00:
                    txt = 'RTID(0)'
                else:
                    raise ValueError(f'RTID subtype {sub:#x}')
            else:
                txt = 'RTID(0)'
            return RTID(txt, b[start:self.i])
        if t == 0x85: return self.obj()
        if t == 0x86:
            assert b[self.i] == 0xfd; self.i += 1
            n, self.i = _rvar(b, self.i)
            arr = [self.val() for _ in range(n)]
            assert b[self.i] == 0xfe; self.i += 1
            return arr
        raise ValueError(f'unknown tag {t:#x} at {self.i - 1}')

    def obj(self):
        d = {}
        while self.b[self.i] != 0xff:
            t = self.b[self.i]; self.i += 1
            k = self.str_(t)
            d[k] = self.val()
        self.i += 1
        return d


def decode(b):
    assert b[:4] == b'RTON', 'not RTON (encrypted pp.dat?)'
    r = _Reader(b); r.i = 8
    root = r.obj()
    assert b[r.i:r.i + 4] == b'DONE'
    return root


class _Writer:
    def __init__(self):
        self.out, self.sc = bytearray(), {}

    def str_(self, s):
        try:
            raw = s.encode('latin1'); ascii_ok = raw.isascii()
        except UnicodeEncodeError:
            ascii_ok = False
        if ascii_ok and getattr(s, 'tag', 0) == 0x81:
            self.out += b'\x81' + _wvar(len(raw)) + raw
        elif not ascii_ok or getattr(s, 'tag', 0) == 0x82:
            u = s.encode('utf-8')
            self.out += b'\x82' + _wvar(len(s)) + _wvar(len(u)) + u
        elif s in self.sc:
            self.out += b'\x91' + _wvar(self.sc[s])
        else:
            self.sc[s] = len(self.sc)
            self.out += b'\x90' + _wvar(len(raw)) + raw

    def val(self, v):
        o = self.out
        if isinstance(v, RTID): o += v.raw
        elif isinstance(v, bool): o.append(int(v))
        elif isinstance(v, RFloat):
            o.append(v.tag)
            if v.tag == 0x22: o += struct.pack('<f', v)
            elif v.tag == 0x42: o += struct.pack('<d', v)
        elif isinstance(v, float):
            o.append(0x42); o += struct.pack('<d', v)
        elif isinstance(v, int):
            t = v.tag if isinstance(v, RInt) else 0x25
            o.append(t)
            if t in _FIX: o += struct.pack('<' + _FIX[t], v)
            elif t in (0x24, 0x28, 0x44, 0x48): o += _wvar(v)
            elif t in (0x25, 0x29, 0x45, 0x49): o += _wvar((v << 1) ^ (v >> 63))
        elif isinstance(v, str): self.str_(v)
        elif isinstance(v, list):
            o += b'\x86\xfd' + _wvar(len(v))
            for x in v: self.val(x)
            o.append(0xfe)
        elif isinstance(v, dict):
            o.append(0x85); self.obj(v)
        else:
            raise TypeError(type(v))

    def obj(self, d):
        for k, v in d.items():
            self.str_(k); self.val(v)
        self.out.append(0xff)


def encode(root):
    w = _Writer()
    w.out += b'RTON\x01\x00\x00\x00'
    w.obj(root)
    w.out += b'DONE'
    return bytes(w.out)
