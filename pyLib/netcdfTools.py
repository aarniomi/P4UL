#!/usr/bin/env python


# !/home/mjsauvin/python/bin/python

import netCDF4 as nc
import sys
import argparse
import numpy as np

debug = True

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def asciiEncode(uList, uStr):
  n = len(uList)
  if(n > 0):
    uList = list(uList)  # This might be a tuple coming in
    for i in xrange(len(uList)):
      uList[i] = uList[i].encode('ascii')
  else:
    print(' Dictionary {} has zero length. Exiting ...'.format(uStr))
    sys.exit(1)

  return uList

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def netcdfDataset(filename, verbose=True):
  # Create Dataset
  ds = nc.Dataset(filename)

  # Generate a list of variables and independent variables contained in the file.
  varList = asciiEncode(ds.variables.keys(), 'Variables')
  dimList = asciiEncode(ds.dimensions.keys(), 'Dimensions')

  if(verbose):
    print(' Variable List : {} '.format(varList))
    print(' Dimension List : {} '.format(dimList))

  return ds, varList, dimList

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def netcdfOutputDataset(filename, mode='w'):
  dso = nc.Dataset(filename, mode, format='NETCDF4')
  return dso

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def netcdfWriteAndClose(dso):
  print('Writing of output data  .... ')
  dso.close()
  print(' ... done. File closed.')

  dso = None

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def read1DVariableFromDataset(varStr, ds, checkList, iLOff=0, iROff=0, cl=1):
  # iLOff: left offset
  # iROff: right offset
  # cl   : coarsening level
  if(varStr in checkList):

    try:
      print(' Reading variable {} ... '.format(varStr))
      if(iROff == 0):
        var = ds.variables[varStr][(0 + iLOff):]
      else:
        var = ds.variables[varStr][(0 + iLOff):-abs(iROff)]
      print(' ... done.')
    except:
      print(' Cannot read the array of variable: {}.'.format(varStr))
      sys.exit(1)

  else:
    print(' Variable {} not in list {}.'.format(varStr, checkList))
    sys.exit(1)

  return var[::cl], np.shape(var[::cl])

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def readVariableFromDataset(varStr, ds, checkList):
  if(varStr in checkList):
    vds = ds.variables[varStr]
    dlist = asciiEncode(vds.dimensions, ' Variable dimensions ')

    # Load the independent variables and wrap them into a dict
    dDict = dict()
    for dname in dlist:
      dData = ds.variables[dname][:]
      dDict[dname] = dData
      dData = None

    # Then the dependent variable. When all is extracted, no need to know the shape
    var = vds[:]

  else:
    sys.exit(' Variable {} not in list {}.'.format(varStr, checkList))

  return var, dDict

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def read3DVariableFromDataset(varStr, ds, checkList, iTOff=0, iLOff=0, iROff=0, cl=1, meanOn=False):
  # iLOff: left offset
  # iROff: right offset
  # cl   : coarsening level
  if(varStr in checkList):

    iL = 0 + iLOff
    iR = abs(iROff)
    iT = 0 + iTOff
    try:
      print(' Reading variable {} ... '.format(varStr))
      if(iR == 0):
        # Param list (time, z, y, x )
        if(meanOn):
          var = ds.variables[varStr][iL:, iL:, iL:]
        else:
          var = ds.variables[varStr][iT:, iL:, iL:, iL:]
      else:
        if(meanOn):
          var = ds.variables[varStr][iL:-iR, iL:-iR, iL:-iR]
        else:
          var = ds.variables[varStr][iT:, iL:-iR, iL:-iR, iL:-iR]
      print(' ... done.')
    except:
      print(' Cannot read the array of variable: {}.'.format(varStr))
      sys.exit(1)

  else:
    print(' Variable {} not in list {}.'.format(varStr, checkList))
    sys.exit(1)

  if(meanOn):
    vo = var[::cl, ::cl, ::cl]; vo_dims = np.shape(vo)
  else:
    vo = var[:, ::cl, ::cl, ::cl]; vo_dims = np.shape(vo)

  var = None

  return vo, vo_dims

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def interpolatePalmVectors(v0, v0_dims, cmpStr, meanOn=False):

  icmp = int()
  iOn = False
  jOn = False
  kOn = False
  if(cmpStr == 'i'):
    icmp = 3
    iOn = True
  elif(cmpStr == 'j'):
    icmp = 2
    jOn = True
  elif(cmpStr == 'k'):
    icmp = 1
    kOn = True
  else:
    print('Invalid component string: {}. Exiting ...'.format(cmpStr))
    sys.exit(1)

  vc_dims = np.array(v0_dims)
  vc_dims[1:] -= 1  # Reduce spatial dimension by one.

  vc = np.zeros(vc_dims)
  if(meanOn):
    vm = np.zeros(vc_dims[1:])
  else:
    vm = np.array([])  # Empty array.

  # Create index arrays for interpolation.
  jl = np.arange(0, vc_dims[icmp]); jr = jl + 1  # x,y,z: left < right

  nTimes = v0_dims[0]
  for i in xrange(nTimes):
    tmp0 = v0[i, :, :, :].copy()

    if(iOn):
      tmp1 = (tmp0[:, :, jl] + tmp0[:, :, jr]) * 0.5; tmp0 = None
      tmp2 = tmp1[1:, 0:-1, :]
    if(jOn):
      tmp1 = (tmp0[:, jl, :] + tmp0[:, jr, :]) * 0.5; tmp0 = None
      tmp2 = tmp1[1:, :, 0:-1]
    if(kOn):
      tmp1 = (tmp0[jl, :, :] + tmp0[jr, :, :]) * 0.5; tmp0 = None
      tmp2 = tmp1[:, 0:-1, 0:-1]
    tmp1 = None

    vc[i, :, :, :] = tmp2

    if(meanOn):
      vm += tmp2.copy()

  # Clear memory.
  tmp0 = None
  tmp1 = None
  tmp2 = None

  if(meanOn):
    vm /= float(nTimes)

  print(' Interpolation along the {}^th direction completed.'.format(cmpStr))

  return vc, vm    # vm is empty if meanOn=False.

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def vectorPrimeComponent(vc, vm):
  vc_dims = np.shape(vc)
  vp = np.zeros(np.shape(vc))

  nTimes = vc_dims[0]
  print(' Computing primes for {} times ... '.format(nTimes))

  for i in xrange(nTimes):
    vp[i, :, :, :] = vc[i, :, :, :] - vm[:, :, :]

  print(' ... done.')

  return vp


# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*

def createNetcdfVariable(dso, v, vName, vLen, vUnits, vType, vTuple, parameter, zlib=False):

  if(parameter):
    dso.createDimension(vName, vLen)
  var = dso.createVariable(vName, vType, vTuple, zlib=zlib)
  var.units = vUnits
  var[:] = v
  v = None

  if(parameter):
    pStr = 'parameter'
  else:
    pStr = 'variable'

  print ' NetCDF {} {} successfully created. '.format(pStr, vName)

  return var

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def createCoordinateAxis(dso, Rdims, Rdpx, axis, varname, formatstr, unit, parameter, zlib=False):
  arr = np.empty(Rdims[axis])
  for i in xrange(Rdims[axis]):
    # dpx is in [N,E], see getGeoTransform() in gdalTools.py
    arr[i] = i * Rdpx[axis]
  axvar = createNetcdfVariable(dso, arr, varname, len(
      arr), varname, formatstr, (varname,), parameter, zlib)
  arr = None
  return axvar

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*


def fillTopographyArray(Rtopo, Rdims, Rdpx, datatype):
  topodims = np.array([Rdims[2], Rdims[0], Rdims[1]])
  topo = np.zeros(topodims, dtype=datatype)
  print(' \n Filling 3D array from topography data...')
  print(' Dimensions [z,y,x]: [{}, {}, {}]'.format(*topodims))
  print(' Total number of data points: {}'.format(np.prod(topodims)))
  for x in xrange(Rdims[1]):
    for y in xrange(Rdims[0]):
      # Reverse the y-axis because of the top-left origo in raster
      maxind = int(round(Rtopo[-y - 1][x] / Rdpx[2]))
      topo[0:maxind, y, x] = 1
  print(' ...done. \n')
  return topo

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
