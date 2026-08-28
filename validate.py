import os
import sys
from dspcompliance import DspCompliance
import argparse
import logging

logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)
logger.addHandler(handler)

# validates an online or offline installation
# for partial schema files, requires external refs of the following form:
# (cannot start with / )
# "$ref": "schema.json#/path/to/subschema"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True, help="json file")
    parser.add_argument("--schema", required=True, help="schema file")
    args = parser.parse_args()

    infile = args.infile
    schemafile = args.schema
    if not os.path.exists(infile):
        sys.exit("error - file %s does not exist" % infile)
    if not os.path.exists(schemafile):
        sys.exit("error - file %s does not exist" % schemafile)

    dspc = DspCompliance(infile, schemafile)

    if dspc.validate():
        sys.exit("validated correctly")

    sys.exit("validation failed")