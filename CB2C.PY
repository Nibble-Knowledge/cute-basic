#!/usr/bin/python
import sys
# This if only runs if this file is called as a script - if it is included, it doesn't
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print 'No file specified'
		quit()
	inputf = open(sys.argv[1])
	line = inputf.readline()
	linenum = 1
	# Flags for program START and END - one per program
	hasstart = 0
	hasend = 0
	output = []
	# Header for all CUTE BASIC compilations
	output.append("#include \"CBSTDLIB.H\"")
	# Basic nibble type
	output.append("typedef struct _nib")
	output.append("{")
	output.append("unsigned int data : 4;")
	output.append("unsigned int pad : 4;")
	output.append("} nib;")
	# list of variable names
	varnames = []
	while(line != ""):
		# Check for the start
		if line.strip() == "START":
			if hasstart == 1:
				print "START already declared"
			else:
				hasstart = 1
				output.append("int main()")
				output.append("{")
				# Some fun
				output.append("puts(HEADER);")
				output.append("puts(\"\");")
		elif line.strip() == "END":
			if hasend == 1:
				print "END already declared"
			else:
				hasend = 1
				output.append("return 0;")
				output.append("}")
		splitline = line.split()
		# Variable declaration and initalisation
		# LET - specifically declaration
		if splitline[0] == "LET":
			for i in varnames:
				if i == splitline[1]:
					print "Variable name " + splitline[1] + " already declared!"
					quit(1)
			# The variable name will be the second whitespace delimited field
			varnames.append(splitline[1])
			# AS - initialisation
			if splitline[2] == "AS":
				if int(splitline[3]) > 16:
					print "Variable " + splitline[1] + " too big!"
					quit(1)
				output.insert(6, "typedef struct _nibx" + splitline[3])
				output.insert(7, "{")
				# Firstly, check if we're using SIGNED or UNSIGNED - if neither, UNSIGNED.
				if len(splitline) <= 6 or splitline[6] == "UNSIGNED":
					# Try to match requested size with variable size in C. The next field after as is the size in nibbles (so the first if is less than 3 nibbles or 16 bits)
					if int(splitline[3]) <= 3:
						output.insert(8, "unsigned short int data : " + str(int(splitline[3]) * 4) + ";")
					elif int(splitline[3]) > 3 and int(splitline[3]) <= 8:
						output.insert(8, "unsigned int data : " + str(int(splitline[3]) * 4) + ";")
					elif int(splitline[3]) > 8 and int(splitline[3]) <= 16:
						output.insert(8, "unsigned long long data : " + str(int(splitline[3]) * 4) + ";")
				elif len(splitline) > 6 and splitline[6] == "SIGNED":
					# Signed version
					if int(splitline[3]) <= 3:
						output.insert(8, "short int data : " + str(int(splitline[3]) * 4) + ";")
					elif int(splitline[3]) > 3 and int(splitline[3]) <= 8:
						output.insert(8, "int data : " + str(int(splitline[3]) * 4) + ";")
					elif int(splitline[3]) > 8 and int(splitline[3]) <= 16:
						output.insert(8, "long long data : " + str(int(splitline[3]) * 4) + ";")
				# Padding - you cannot have a non-multiple of 8 bits on an x86 machine.
				if (int(splitline[3]) % 8) <= 3:
					output.insert(9, "unsigned short int pad : " + str(int(splitline[3]) % 8) + ";")
				elif int(splitline[3]) % 8 > 3 and int(splitline[3]) % 8 <= 8:
					output.insert(9, "unsigned int data : " + str(int(splitline[3]) % 8) + ";")
				elif int(splitline[3]) % 8 > 8 and int(splitline[3]) % 8 <= 16:
					output.insert(9, "unsigned long long data : " + str(int(splitline[3]) % 8) + ";")
				# BTW reader, this inserts to a static place in the list so all new variable do have a place... faster then checking!
				output.insert(10, "} nibx" + splitline[3] + ";")
				output.append("nibx" + splitline[3] + " " + splitline[1] + ";")
				if len(splitline) > 4 and splitline[4] == "BE":
					output.append(splitline[1] + ".data = " + splitline[5] + ";")
			else:
				output.append("nib " + splitline[1] + ";")
				if splitline[2] == "BE":
					output.append(splitline[1] + ".data = " + splitline[3] + ";")
					
		#Math, with assignment as the first thing on the line
		elif ((splitline[0] in varnames) and splitline[1] == "BE"): 
			vartypes = ["BINARY", "HEX", "CHAR"]
			vartype = ""
			if(splitline[2] in ["COMPLEMENT", "NEGATE", "INCREMENT", "DECREMENT", "NOT"]):
				
				if splitline[3] in vartypes:
					vartype = splitline[3]
					splitline.remove(splitline[3])
					if vartype == "BINARY":
						splitline[3] = "0b" + splitline[3]
					elif vartype == "HEX":
						splitline[3] = "0x" + splitline[3]
					elif vartype[3] == "CHAR":
						splitline[3] = "\'" + splitline[3] + "\'"
				else:
					splitline[3] = splitline[3] + ".data"
				#unary math/bit/logic operators
				if splitline[2] == "COMPLEMENT":
					output.append(splitline[0] + ".data = ~" + splitline[3] + ";")
				elif splitline[2] == "NEGATE":
					output.append(splitline[0] + ".data = -" + splitline[3] + ";")
				elif splitline[2] == "INCREMENT":
					output.append(splitline[0] + ".data = " + splitline[3] + " + 1;")
				elif splitline[2] == "DECREMENT":
					output.append(splitline[0] + ".data = " + splitline[3] + " - 1;")
				elif splitline[2] == "NOT":
					output.append(splitline[0] + ".data = !" + splitline[3] + ";")
			
			if splitline[2] in vartypes:
				vartype = splitline[2]
				splitline.remove(splitline[2])
				if vartype == "BINARY":
					splitline[2] = "0b" + splitline[2]
				elif vartype == "HEX":
					splitline[2] = "0x" + splitline[2]
				elif vartype[2] == "CHAR":
					splitline[2] = "\'" + splitline[2] + "\'"
			else:
				splitline[2] = splitline[2] + ".data"
				
			if len(splitline) > 4:
				if splitline[4] in vartypes:
					vartype = splitline[4]
					splitline.remove(splitline[4])
					if vartype == "BINARY":
						splitline[4] = "0b" + splitline[4]
					elif vartype == "HEX":
						splitline[4] = "0x" + splitline[4]
					elif vartype[4] == "CHAR":
						splitline[4] = "\'" + splitline[4] + "\'"
				else:
					splitline[4] = splitline[4] + ".data"
				
			#binary math operators
			if splitline[3] == "ADD":
				output.append(splitline[0] + ".data = " + splitline[2] + " + " + splitline[4] + " ;")
			elif splitline[3] == "SUBTRACT":
				output.append(splitline[0] + ".data = " + splitline[2] + " - " + splitline[4] + " ;")
			elif splitline[3] == "MULTIPLY":
				output.append(splitline[0] + ".data = " + splitline[2] + " * " + splitline[4] + " ;")
			elif splitline[3] == "DIVIDE":
				output.append(splitline[0] + ".data = " + splitline[2] + " / " + splitline[4] + " ;")
			elif splitline[3] == "MODULUS":
				output.append(splitline[0] + ".data = " + splitline[2] + " % " + splitline[4] + " ;")
			
			#binary bitwise operators
			elif splitline[3] == "AND":
				output.append(splitline[0] + ".data = " + splitline[2] + " & " + splitline[4] + " ;")
			elif splitline[3] == "NAND":
				output.append(splitline[0] + ".data = ~(" + splitline[2] + " & " + splitline[4] + ") ;")
			elif splitline[3] == "OR":
				output.append(splitline[0] + ".data = " + splitline[2] + " | " + splitline[4] + " ;")
			elif splitline[3] == "NOR":
				output.append(splitline[0] + ".data = ~(" + splitline[2] + " | " + splitline[4] + ") ;")
			elif splitline[3] == "XOR":
				output.append(splitline[0] + ".data = " + splitline[2] + " ^ " + splitline[4] + ";")
			elif splitline[3] == "XNOR":
				output.append(splitline[0] + ".data = ~(" + splitline[2] + " ^ " + splitline[4] + ") ;")
				
			#binary logical operators
			elif splitline[3] == "ALSO":
				output.append(splitline[0] + ".data = " + splitline[2] + " && " + splitline[4] + ";")
			elif splitline[3] == "EITHER":
				output.append(splitline[0] + ".data = " + splitline[2] + " || " + splitline[4] + ";")
				
			#Logical tests
			elif splitline[3] == "EQUALS":
				output.append(splitline[0] + ".data = " + splitline[2] + " == " + splitline[4] + ";")

		#Conditionals
		#If/else/elseif/endif
		elif splitline[0] == "IF":
			output.append("if (" + splitline[1] + ") {")
		elif splitline[0] == "ELSEIF":
			output.append("else if (" + splitline[1] + ") {")
		elif splitline[0] == "ELSE":
			output.append("else {")
		elif splitline[0]== "ENDIF":
			output.append("}")
		
		#Loopwhile/Endloop
		if splitline[0] == "LOOPWHILE":
			output.append("while (" + splitline[1] + ") {")
			
			
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
