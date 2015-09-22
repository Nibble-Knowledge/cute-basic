#!/usr/bin/python
import sys

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print 'No file specified'
		quit()
	inputf = open(sys.argv[1])
	line = inputf.readline()
	linenum = 1
	hasstart = 0
	hasend = 0
	output = []
	output.append("typedef struct _nib")
	output.append("{")
	output.append("unsigned int data : 4;")
	output.append("unsigned int pad : 4;")
	output.append("} nib;")
	varnames = []
	while(line != ""):
		if line.strip() == "START":
			if hasstart == 1:
				print "START already declared"
			else:
				hasstart = 1
				output.append("int main()")
				output.append("{")		
		elif line.strip() == "END":
			if hasend == 1:
				print "END already declared"
			else:
				hasend = 1
				output.append("return 0;")
				output.append("}")
		splitline = line.split()
		if splitline[0] == "LET":
			for i in varnames:
				if i == splitline[1]:
					print "Variable name " + splitline[1] + " already declared!"
					quit(1)
			varnames.append(splitline[1])
			if splitline[2] == "AS":
				if int(splitline[3]) > 16:
					print "Variable " + splitline[1] + " too big!"
					quit(1)
				output.insert(5, "typedef struct _nibx" + splitline[3])
				output.insert(6, "{")
				output.insert(7, "unsigned long data : " + str(int(splitline[3]) * 4) + ";")
				output.insert(8, "unsigned long pad : " + str(int(splitline[3]) % 8) + ";")
				output.insert(9, "} nibx" + splitline[3] + ";")
				output.append("nibx" + splitline[3] + " " + splitline[1] + ";");
				if splitline[4] == "BE":
					output.append(splitline[1] + ".data = " + splitline[5] + ";")
			else:
				output.append("nib " + splitline[1] + ";")
				if splitline[2] == "BE":
					output.append(splitline[1] + ".data = " + splitline[3] + ";")
		line = inputf.readline()
		linenum = linenum + 1
	inputf.close()
	if hasstart == 0:
		print "No START declared!"
		quit(1)
	if hasend == 0:
		print "No END declared!"
		quit(1)
	if hasend == 1 and hasstart == 1:
		for i in output:
			print i
	quit(0)
