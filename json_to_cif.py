import json
import os
import sys
import argparse
from collections import OrderedDict

"""
author James Smith 2026
does not retain comments
does not retain "." as opposed to "?" (deconverts to ?)
for datablocks > 1, convert each separately, then concatenate into a single mmcif file
fixed
    did not retain dictionary order
    multiline strings
    first data block name
    negative numbers converting to strings
    modularize
    strings inconsistently quoted
    retain data blocks > 1
    enable extended ids (no fix required?)
tasks:
    improve tabular formatting?
    does not retain "." as opposed to "?" (deconverts to ?)
"""

def get_next_value(v:str | float | int | None) -> str:
    """get value from string, removing quotes and converting to string
    args:
        v (str | float | int | None): value to convert
    returns:
        cif-encoded string
    raises:
        ValueError: if value is boolean, list, or dictionary
    """
    if v is None:
        return "?"
    elif isinstance(v, str):
        if v.find("\n") < 0:
            tokens = v.split()
            if len(tokens) == 1:
                return v
            # quote multi-word string
            if v.find("'") >= 0:
                return '"%s"' % v.replace('"', "'")
            return "'%s'" % v.replace("'", "")
        else:
            return convert_multiline_string(v)
    elif isinstance(v, float) or isinstance(v, int):
        return str(v)
    elif isinstance(v, bool):
        # supported in mmcif?
        raise ValueError("error - boolean values not supported")
    elif isinstance(v, list) or isinstance(v, dict):
        # supported in mmcif?
        raise ValueError("error - nested lists or dictionaries not supported")

def convert_multiline_string(s:str) -> str:
    """convert json string with newlines to mmcif multiline string
    args:
        s (str): string to convert
            should have only internal newlines
    returns:
        str: mmcif multiline string
            regardless of cardinality, should always start with \n; and end with \n;\n
        issue:
            problem for two in a row, blank line in between
                solution - external code must replace consecutive newlines with one newline
    """
    if s.find("\n") < 0:
        return s
    tokens = s.split("\n")
    s = "\n;" + "\n".join(tokens) + "\n;\n"
    return s

def converter(d:dict, outfile:str) -> bool:
    """convert python dictionary to cif
    args:
        d (dict): python dictionary to convert
        outfile (str): output cif file path
    returns:
        status (bool): success or failure
    """

    outlabel = os.path.splitext(os.path.basename(outfile).upper())[0]

    with open(outfile, "w") as w:
        try:
            # begin one data section
            w.write("data_%s\n" % outlabel)
            w.write("#\n")
            # read category keys
            for key,val in d.items():
                # read attribute: value pairs
                # test for unit cardinality
                if isinstance(val, dict):
                    # value is one dictionary
                    val = OrderedDict(val)
                    # print one _key.attribute: value per line (unless have multiline value)
                    for k,v in val.items():
                        v = get_next_value(v)
                        if v.endswith("\n"):
                            w.write("_%s.%s\t%s" % (key, k, v))
                        else:
                            w.write("_%s.%s\t%s\n" % (key, k, v))
                # test for loop
                elif isinstance(val, list):
                    # value is list of dictionaries
                    # print loop header
                    w.write("loop_\n")
                    # print attributes section (one _key.attribute per line)
                    for dct in val:
                        if not isinstance(dct, dict):
                            raise ValueError("error - list must contain dictionaries")
                        dct = OrderedDict(dct)
                        # get attributes from first dictionary
                        for k in dct.keys():
                            w.write("_%s.%s\n" % (key, k))
                        # exit after first dictionary
                        break
                    # print values section
                    for dct in val:
                        if not isinstance(dct, dict):
                            raise ValueError("error - list must contain dictionaries")
                        dct = OrderedDict(dct)
                        # print values record on one line (unless have multiline value)
                        record = ""
                        for v in dct.values():
                            v = get_next_value(v)
                            record += v
                            if not record.endswith("\n"):
                                record += "\t"
                        # handle consecutive multiline values
                        record = record.replace("\n\n", "\n")
                        # write one record
                        w.write(record)
                        if not record.endswith("\n"):
                            w.write("\n")
                else:
                    raise ValueError("error - unrecognized data type %s" % type(val))
                # wrap one category section
                w.write("#\n")
        except ValueError as e:
            print("Value Error: " + str(e))
            return False
        except Exception as e:
            print("Exception: " + str(e))
            return False

    return True


if __name__ == "__main__":

    # e.g. python3 json_to_cif.py --infile 3hhb.json --outfile 3hhb.cif

    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True, help="json file")
    parser.add_argument("--outfile", required=True, help="cif file")
    parser.add_argument("--dict", action="store_true", help="input file is a python dictionary rather than json")

    # parse args
    args = parser.parse_args()

    # validate file paths
    infile = args.infile
    outfile = args.outfile
    if not os.path.exists(infile):
        sys.exit("error - file %s does not exist" % infile)

    # find name for data block
    inlabel = os.path.splitext(os.path.basename(infile).upper())[0]
    outlabel = os.path.splitext(os.path.basename(outfile).upper())[0]
    assert inlabel == outlabel, "input and output pdb ids must be the same %s %s" % (inlabel, outlabel)

    # convert json file to python dictionary
    if not args.dict:
        with open(infile, "r") as r:
            data = json.load(r)
    else:
        with open(infile, "r") as r:
            data = eval(r.read())
    data = OrderedDict(data)

    # convert python dictionary to cif
    if not converter(data, outfile):
        sys.exit("error - conversion failed")

    print("wrote final result to %s" % outfile)
    print("conversion complete")