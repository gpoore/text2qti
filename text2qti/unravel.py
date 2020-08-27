# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Glenn Horton-Smith
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#

def unravel(i, b):
    '''
    Breaks up a flat index i into a list of coordinates
    of dimension len(b) with sizes given by array b.
    Equivalent to numpy.unravel_index(), except always returns
    indexes in 'F' order, and is faster.
    '''
    o = [0]*len(b)
    for ii in range(len(b)):
       o[ii] = i%b[ii]
       i //= b[ii]
    return o
