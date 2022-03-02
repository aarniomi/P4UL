#!/usr/bin/env python3
import sys
import argparse
import numpy as np
from mapTools import *
from utilities import filesFromList, writeLog
from plotTools import addImagePlot
import matplotlib.pyplot as plt
'''
Author: Mikko Auvinen
        mikko.auvinen@helsinki.fi
        University of Helsinki &
        Finnish Meteorological Institute
'''

#==========================================================#
parser = argparse.ArgumentParser(prog='tif2NumpyTile.py')
parser.add_argument("-f", "--filename",type=str, help="Input tif-image file name.")
parser.add_argument("-fo", "--fileout",type=str, help="Output npz file name.")
parser.add_argument("-r", "--reso",type=float, nargs=2, \
                    help="Resolution of the tif-image [Dx Dy].")
parser.add_argument("-xo", "--xorig",type=float, nargs=2,default=[0.,0.],\
  help="Coords [N,E] of the tif-images top-left corner. Default=[0,0]")
parser.add_argument("-p", "--printOn", help="Print the numpy array data.",\
  action="store_true", default=False)
parser.add_argument("-pp", "--printOnly", help="Only print the numpy array data. Don't save.",\
  action="store_true", default=False)
parser.add_argument("-s", "--scale",type=float, default=1.,\
   help="Scale factor for the output. Default=1.")
parser.add_argument("-a", "--ascii", action="store_true", default=False, \
   help="Input is an ASCII-formatted raster with no metadata (such as TOPOGRAPHY_DATA). Default=False.")
args = parser.parse_args()
writeLog( parser, args, args.printOnly )
#==========================================================#

# Renaming, nothing more.
filename  = args.filename
fileout   = args.fileout
reso      = args.reso
ROrig     = args.xorig
printOn   = args.printOn
printOnly = args.printOnly
sc        = args.scale
ascii     = args.ascii

if(ascii):
  R = np.loadtxt(filename)
else:
  R = openTifAsNumpy(filename)

dPx      = np.array([sc*reso[0], sc*reso[1]])
Rdict = {'R' : R, 'GlobOrig' : ROrig, 'gridRot' : 0., 'dPx' : dPx}

if( not printOnly ):
  print(' Writing file {} ... '.format(fileout) )
  saveTileAsNumpyZ( fileout, Rdict)
  print(' ... done! ')

if( printOn or printOnly ):
  pfig = plt.figure(num=1, figsize=(10.,10.))
  pfig = addImagePlot( pfig, R, fileout, gridOn=True )
  plt.show()
