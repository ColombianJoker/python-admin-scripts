#!/usr/bin/python

import os
import string
import re

# get selected text from shell:
text = os.getenv('TM_SELECTED_TEXT')

# find all numbers following a $ in selection:
p = re.compile('\$[-+]?([0-9]*\.[0-9]+|[0-9]+)')

result = p.findall(text)
sum_num = sum([float(i) for i in result])
result = ["$"+i for i in result]

output_str = string.join(result, " + ")

print "Sum of costs in selected text:"
print output_str, "= $"+str(sum_num)
