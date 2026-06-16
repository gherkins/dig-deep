"""Make `digdeep` importable when running tests from a checkout without installing."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
