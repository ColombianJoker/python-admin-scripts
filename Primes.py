#!/usr/bin/python


#numpy solution

import numpy
def primesfrom2to(n):
	""" Input n>=6, Returns a array of primes, 2 <= p < n """
	sieve = numpy.ones(n/3 + (n%6==2), dtype=numpy.bool)
	sieve[0] = False
	for i in xrange(int(n**0.5)/3+1):
		if sieve[i]:
			k=3*i+1|1
			sieve[			((k*k)/3)			::2*k] = False
			sieve[(k*k+4*k-2*k*(i&1))/3::2*k] = False
	return numpy.r_[2,3,((3*numpy.nonzero(sieve)[0]+1)|1)]

#pure-python solution

def primes1(n):
	""" Returns	a list of primes < n """
	sieve = [True] * (n/2)
	for i in xrange(3,int(n**0.5)+1,2):
		if sieve[i/2]:
			sieve[i*i/2::i] = [False] * ((n-i*i-1)/(2*i)+1)
	return [2] + [2*i+1 for i in xrange(1,n/2) if sieve[i]]

def primes2(n):
	""" Input n>=6, Returns a list of primes, 2 <= p < n """
	correction = (n%6>1)
	n = {0:n,1:n-1,2:n+4,3:n+3,4:n+2,5:n+1}[n%6]
	sieve = [True] * (n/3)
	sieve[0] = False
	for i in xrange(int(n**0.5)/3+1):
		if sieve[i]:
			k=3*i+1|1
			sieve[			((k*k)/3)			::2*k]=[False]*((n/6-(k*k)/6-1)/k+1)
			sieve[(k*k+4*k-2*k*(i&1))/3::2*k]=[False]*((n/6-(k*k+4*k-2*k*(i&1))/6-1)/k+1)
	return [2,3] + [3*i+1|1 for i in xrange(1,n/3-correction) if sieve[i]]

# Main

print primesfrom2to(2000)
