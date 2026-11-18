"""Loads the per-zone configuration module named by $EQ_ZONE (see tools/zones/)."""
import importlib,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
Z=importlib.import_module('zones.'+os.environ['EQ_ZONE'])
MAP_DIR=os.environ['EQ_MAP_DIR']
OUT_DIR=os.environ.get('EQ_OUT_DIR','.')
