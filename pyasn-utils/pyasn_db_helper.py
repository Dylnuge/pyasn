# Copyright (c) 2009-2014 Hadi Asghari
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# TODO: COMPLETE / convert to script / test final version on both py3 & 2 (for the bytestring/unicode stuff)
# todo: perhaps some of the other python files would also be better combinet with this

from __future__ import print_function, division
import socket, struct
import pickle, zlib
import time

def convert_ipasndb_to_binary(ipasndb_file, asnames_file, binary_outfile):
    fw = open(binary_outfile, 'wb')
    # SHOW STRUCTURE ADD HEADER-VER to binary file to show ipasn version + date
    fw.write(str.encode('PYASN'))  # magic header
    fw.write(b'\x01')  # binary format version 1
    fw.write(struct.pack('I', 0))  # number of records; will need to be updated at the end.
    nbytes = 12
    
    # let's store as comments the name of the input files used to build the binary file. good for debugging.
    comments = "Created '%s', from ipasndb: %s, asnames: %s." % (time.actime(), ipasndb_file, asnames_file)
    comments = comments.encode('ASCII', errors='replace')[:499] + b'\0'  # convert to bytes, trim, terminate
    fw.write(struct.pack('h', len(comments)))
    fw.write(comments)
    nbytes += len(comments)

    with open(ipasndb_file) as f:
        nrecs = 0
        for s in f:
            if s[0] == '#' or s[0]=='\n' or s[0] == ';':
                continue
            prefix, asn = s[:-1].split()
            asn = int(asn)
            network, cidr = prefix.split('/')
            cidr = int(cidr)
            nbytes += fw.write(socket.inet_aton(network))
            nbytes += fw.write(struct.pack('B', cidr))
            nbytes += fw.write(struct.pack('I', asn))
            nrecs += 1

    fw.write(bytes(9))  # write one zero record
    if asnames_file:
        # todo: i'm not sure this is the best way to store this
        d = load_asnames_dict(asnames_file)
        z = zlib.compress(pickle.dumps(d))
        fw.write(struct.pack('I', len(z)))  # number of bytes
        fw.write(z)
    # almost done. update number of records at start of file.
    fw.seek(6)
    fw.write(struct.pack('I', nrecs))
    fw.close()    
    return nbytes, nrecs
             

def load_asnames_dict(filein):
    # loads an as-names file into a dictionary
    # current format: one per line, space after ASN, 32bits with dots
    # todo: chose format of this file based on final decisions in pyasn.pyasn()
    asnames = {}
    f = open(filein, encoding='utf-8')  # todo: Test on py2 (re utf/bytes).
    for s in f:
        asn, asname = s[:-1].split(maxsplit=1)
        if asname == '-Reserved AS-':
            continue
        asn = int(asn[2:]) if '.' not in asn else int(asn[2:asn.find('.')])*65536 +  int(asn[asn.find('.')+1:]) 
        asnames[asn] = asname
    f.close()
    return asnames
