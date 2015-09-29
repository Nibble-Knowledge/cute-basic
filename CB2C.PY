#!/usr/bin/python
import sys
import os
#stack for keeping track of IF statements - holds line numbers of IF
ifStatementStack = []
#stack for keeping track of LOOPWHILE statements - holds like numbers of LOOPWHILE
loopStatementStack = []
#giant buffer holding output
output = []
#list of names of variables
varnames = []
vartypes = ["BINARY", "HEX", "CHAR"]
varsizes = []
varstofree = []

# This if only runs if this file is called as a script - if it is included, it doesn't
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print 'No file specified'
		quit()
	inputf = open(sys.argv[1])
	linenum = 1
	# Flags for program START and END - one per program
	hasstart = 0
	hasend = 0

	# Header for all CUTE BASIC compilations
	output.append("#include \"CBSTDLIB.H\"")
	
	# Comment for finding the struct declarations
	output.append("/*Structs go here*/")
	output.append("")
	output.append("")
	
	# Basic nibble type
	output.append("typedef struct _nib")
	output.append("{")
	output.append("uint8_t data : 4;")
	output.append("} nib;")
	
	output.append("typedef struct _nibx")
	output.append("{")
	output.append("uint8_t data : 4;")
	output.append("char *extdata;")
	output.append("} nibx;")
	
	output.append("typedef struct _nibxs")
	output.append("{")
	output.append("int8_t data : 4;")
	output.append("char *extdata;")
	output.append("} nibxs;")

	output.append("/*Function declarations go here*/")
	output.append("")
	output.append("")
	
	for line in inputf.readlines():
		# Check for the start
		if line.strip() == "START":
			if hasstart == 1:
				print "START already declared"
			else:
				hasstart = 1
				output.append("")
				output.append("")
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
				output.append("END:")
				output.append("return 0;")
				output.append("}")
		splitline = line.split()
		# Variable declaration and initalisation
		# LET - specifically declaration
		if len(splitline) == 0:
			continue
		if splitline[0] == "LET":
			for i in varnames:
				if len(splitline) > 1 and i == splitline[1]:
					print "Variable name " + splitline[1] + " already declared!"
					quit(1)
			# The variable name will be the second whitespace delimited field
			varnames.append(splitline[1])
			
			structstart = output.index("/*Structs go here*/")
			# AS - initialisation
			if len(splitline) > 2 and splitline[2] == "AS":
				
				'''if int(splitline[3]) > 16:
					print "Variable " + splitline[1] + " too big!"
					quit(1)
				if splitline[3] in varsizes:
					output.append("nibx" + splitline[3] + " " + splitline[1] + ";")
					if len(splitline) > 4 and splitline[4] == "BE":
						output.append(splitline[1] + ".data = " + splitline[5] + ";")
					continue
				output.insert(structstart + 1, "typedef struct _nibx" + splitline[3])
				output.insert(structstart + 2, "{")'''
				# Firstly, check if we're using SIGNED or UNSIGNED - if neither, UNSIGNED.
				if len(splitline) <= 6 or splitline[6] == "UNSIGNED":
					output.append("nibx " + splitline[1] + ";")
					output.append(splitline[1] + ".extdata = malloc(" + str(int(splitline[3]) * 8) + ");")
					varstofree.append(splitline[1])
					'''# Try to match requested size with variable size in C. The next field after as is the size in nibbles (so the first if is less than 3 nibbles or 16 bits)
					if int(splitline[3]) <= 3:
						output.insert(structstart + 3, "unsigned short int data : " + str(int(splitline[3]) * 4) + ";")
					elif int(splitline[3]) > 3 and int(splitline[3]) <= 8:
						output.insert(structstart + 3, "unsigned int data : " + str(int(splitline[3]) * 4) + ";")
					elif int(splitline[3]) > 8 and int(splitline[3]) <= 16:
						output.insert(structstart + 3, "unsigned long long data : " + str(int(splitline[3]) * 4) + ";")'''
				elif len(splitline) > 6 and splitline[6] == "SIGNED":
					output.append("nibxs " + splitline[1] + ";")
					output.append(splitline[1] + ".extdata = malloc(" + str(int(splitline[3]) * 8) + ");")
					varstofree.append(splitline[1])
					'''# Signed version
					if int(splitline[3]) <= 3:
						output.insert(structstart + 3, "short int data : " + str(int(splitline[3]) * 4) + ";")
					elif int(splitline[3]) > 3 and int(splitline[3]) <= 8:
						output.insert(structstart + 3, "int data : " + str(int(splitline[3]) * 4) + ";")
					elif int(splitline[3]) > 8 and int(splitline[3]) <= 16:
						output.insert(structstart + 3, "long long data : " + str(int(splitline[3]) * 4) + ";")
				# Padding - you cannot have a non-multiple of 8 bits on an x86 machine.
				if ((int(splitline[3]) * 4) % 8) > 0 and ((int(splitline[3]) * 4) % 8) <= 3:
					output.insert(structstart + 4, "unsigned short int pad : " + str((int(splitline[3]) * 4) % 8) + ";")
				elif (int(splitline[3]) * 4) % 8 > 3 and (int(splitline[3]) * 4) <= 8:
					output.insert(structstart + 4, "unsigned int pad : " + str((int(splitline[3]) * 4) % 8) + ";")
				elif (int(splitline[3]) * 4) % 8 > 8 and (int(splitline[3]) * 4) % 8 <= 16:
					output.insert(structstart + 4, "unsigned long long pad : " + str((int(splitline[3]) * 4) % 8) + ";")
				else:
					output.insert(structstart + 4, "")
				# BTW reader, this inserts to a static place in the list so all new variable do have a place... faster then checking!
				output.insert(structstart + 5, "} nibx" + splitline[3] + ";")
				output.append("nibx" + splitline[3] + " " + splitline[1] + ";")
				varsizes.append(splitline[3])'''
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
			if(splitline[2] in ["COMPLEMENT", "NEGATE", "INCREMENT", "DECREMENT", "NOT", "ADDRESSOF", "CONTENTOF"]):
				#unary operations
				
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
				elif splitline[2] == "ADDRESSOF":
					output.append(splitline[0] + ".data = &(" + splitline[3] + ");")
				elif splitline[2] == "CONTENTOF":
					output.append(splitline[0] + ".data = *(" + splitline[3] + ");")
			
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
				
			#binary bitshifting
			elif (splitline[3] == "RROTATE" or splitline[3] == "RSHIFT"):
				output.append(splitline[0] + ".data = " + splitline[2] + " >> " + splitline[4] + ";")
			elif (splitline[3] == "LROTATE" or splitline[3] == "LSHIFT"):
				output.append(splitline[0] + ".data = " + splitline[2] + " << " + splitline[4] + ";")
				
			#binary logical operators
			elif splitline[3] == "ALSO":
				output.append(splitline[0] + ".data = " + splitline[2] + " && " + splitline[4] + ";")
			elif splitline[3] == "EITHER":
				output.append(splitline[0] + ".data = " + splitline[2] + " || " + splitline[4] + ";")
				
			#Logical tests
			elif splitline[3] == "EQUALS":
				output.append(splitline[0] + ".data = " + splitline[2] + " == " + splitline[4] + ";")
			elif splitline[3] == "NOTEQUALS":
				output.append(splitline[0] + ".data = " + splitline[2] + " != " + splitline[4] + ";")
			elif splitline[3] == "GREATER":
				output.append(splitline[0] + ".data = " + splitline[2] + " > " + splitline[4] + ";")
			elif splitline[3] == "GREATEREQUALS":
				output.append(splitline[0] + ".data = " + splitline[2] + " >= " + splitline[4] + ";")
			elif splitline[3] == "LESS":
				output.append(splitline[0] + ".data = " + splitline[2] + " < " + splitline[4] + ";")
			elif splitline[3] == "LESSEQUALS":
				output.append(splitline[0] + ".data = " + splitline[2] + " <= " + splitline[4] + ";")

		#Conditionals + GOTO
		elif(splitline[0] in ["IF", "ELSEIF", "ELSE", "ENDIF", "LOOPWHILE", "ENDLOOP", "LOOPAGAIN", "EXITLOOP", "EXITIF", "EARLYEND", "LABEL", "GOTO"]):
			vartypes = ["BINARY", "HEX", "CHAR"]
			vartype = ""
			if len(splitline) > 1 and splitline[1] in vartypes:
				vartype = splitline[1]
				splitline.remove(splitline[1])
				if vartype == "BINARY":
					splitline[1] = "0b" + splitline[1]
				elif vartype == "HEX":
					splitline[1] = "0x" + splitline[1]
				elif vartype[1] == "CHAR":
					splitline[1] = "\'" + splitline[1] + "\'"
			elif len(splitline) > 1:
				splitline[1] = splitline[1] + ".data"
	
			#If/else/elseif/endif
			if splitline[0] == "IF":
				output.append("if (" + splitline[1] + ") {")
				ifStatementStack.append(linenum)
			elif splitline[0] == "ELSEIF":
				output.append("}")
				output.append("else if (" + splitline[1] + ") {")
			elif splitline[0] == "ELSE":
				output.append("}")
				output.append("else {")
			elif splitline[0]== "ENDIF":
				output.append("}")
				output.append("exitif"  + str(ifStatementStack.pop()) + ":")
				output.append(";")
				
			
			#Loopwhile/Endloop
			elif splitline[0] == "LOOPWHILE":
				output.append("while (" + splitline[1] + ") {")
				loopStatementStack.append(linenum)
			elif splitline[0] == "ENDLOOP":
				output.append("}")
				output.append("exitloop" + str(loopStatementStack.pop()) + ":")
				output.append(";")
			
			#GOTO derivatives
			elif splitline[0] == "LOOPAGAIN":
				output.append("continue;")
			elif splitline[0] == "EXITLOOP":
				output.append("goto exitloop" + str(loopStatementStack[-1]) + ";")
			elif splitline[0] == "EXITIF":
				output.append("goto exitif"+ str(ifStatementStack[-1]) + ";")
		
			#GOTO/Labels
			elif splitline[0] == "EARLYEND":
				output.append("goto END;")
			elif splitline[0] == "LABEL":
				output.append(splitline[1] + ":")
			elif splitline[0] == "GOTO":
				output.append("goto " + splitline[1] + ";")
				
		#function declarations
		if splitline[0] == "FUNCTION":
			nextparam =0
			temp = ""
			if len(splitline) > 3 and splitline[2] == "RETURNS":
				temp += "nibx" + splitline[3] + " " + splitline[1] + "("
				nextparam = 4
			else:
				temp += "void " + splitline[1] + "("
				nextparam = 2
			while len(splitline) >= nextparam + 2:
				if splitline[nextparam] != "TAKES" and splitline[nextparam] != "ASWELL":
					nextparam = nextparam + 1
					continue
				temp += "nibx" + splitline[nextparam + 1] + " " + splitline[nextparam + 2]
				nextparam += 3
				if len(splitline) >= nextparam + 2:
					temp += ","
			temp += ");"
			functionindex = output.index("/*Function declarations go here*/")
			output.insert(functionindex + 1, temp)
				
		
		#function definition
		if splitline[0] == "DEFINE":
			#must match declaration sig
			nextparam = 0
			temp = ""
			if len(splitline) > 3 and splitline[2] == "RETURNS":
				temp += "nibx" + splitline[3] + " " + splitline[1] + "("
				nextparam = 4
			else:
				temp += "void " + splitline[1] + "("
				nextparam = 2
			while len(splitline) >= nextparam + 2:
				if splitline[nextparam] != "TAKES" and splitline[nextparam] != "ASWELL":
					nextparam = nextparam + 1
					continue
				temp += "nibx" + splitline[nextparam + 1] + " " + splitline[nextparam + 2]
				nextparam += 3
				if len(splitline) >= nextparam + 2:
					temp += ","
			temp += "){"
			output.append(temp)
		elif splitline[0] == "ENDFUNCTION":
			output.append("}")
		elif splitline[0] == "RETURN":
			output.append("return " + splitline[1] +";")
		elif splitline[0] == "CALL":
			nextparam = 2
			temp = ""
			temp += splitline[1] + "( "
			while len(splitline) > nextparam:
				temp += splitline[nextparam]
				if len(splitline) >= nextparam + 2:
					temp += ", "
				nextparam += 2
			temp += ");"
			output.append(temp)
		
		if splitline[0] == "NOHEADER":
			output.remove("puts(HEADER);")
			output.remove("puts(\"\");")
		
		if splitline[0] == "PRINT":
			if splitline[3] in vartypes:
				vartype = splitline[3]
				splitline.remove(splitline[3])
				if vartype == "BINARY":
					splitline[3] = "0b" + splitline[3]
				elif vartype == "HEX":
					splitline[3] = "0x" + splitline[3]
				elif vartype == "CHAR":
					splitline[3] = "'" + splitline[3] + "'"
			else:
				splitline[3] = splitline[3] + ".extdata[0]"
			if splitline[2] == "CHAR":
				output.append("printf(\"%c\", " + splitline[3] + ");")
			elif splitline[2] == "STRING":
				output.append("printf(\"%s\", " + splitline[3] + ");")
			elif splitline[2] == "UNSIGNED":
				output.append("printf(\"%u\", " + splitline[3] + ");")			
			elif splitline[2] == "SIGNED":
				output.append("printf(\"%i\", " + splitline[3] + ");")
			elif splitline[2] == "BINARY":
				output.append("int binaryread" + str(linenum) + " = " + splitline[3])
				output.append("for(int i = 0; i < " + splitline[1] + "; i++ ) {")
				output.append("if (binaryread" + str(linenum) + " & 1)")
				output.append("{")
				output.append("printf(\"1\");")
				output.append("else")
				output.append("printf(\"0\");")
				output.append("binaryread" + str(linenum) + " >>= 1;")
				output.append("}")
			elif splitline[2] == "HEX":
				output.append("printf(\"%X\", " + splitline[3] + ");")			
			else:
				output.append("printf(\"%u\", " + splitline[3] + ");")
		
		if splitline[0] == "GETKEY":
			output.append(splitline[1] + ".extdata[0] = getchar();")
			
		if splitline[0] == "FILEOUT":
			output.append("FILE *file" + str(linenum) + ";")
			if splitline[1] == "CHAR":
				splitline.remove(splitline[1])
				varout = "\'" + splitline[1] + "\'"
			elif splitline[1] == "UNSIGNED":
				splitline.remove(splitline[1])
				varout = splitline[1]
			elif splitline[1] == "SIGNED":
				splitline.remove(splitline[1])
				varout = "(unsigned char) " + splitline[1]
			elif splitline[1] == "HEX":
				splitline.remove(splitline[1])
				varout = "0x" + splitline[1]
			elif splitline[1] == "BINARY":
				splitline.remove(splitline[1])
				varout = "0b" + splitline[1]
			else:
				varout = splitline[1] + ".extdata[0]"
			if len(splitline) > 3 and splitline[3] == "AT":
				output.append("file" + str(linenum) + " = fopen(\"" + str(splitline[2]) + "\", \"ab+\");")
				if len(splitline) > 4 and splitline[4] in varnames:
					output.append("fseek(file" + str(linenum) + ", " + str(splitline[4]) + ".extdata[0] , SEEK_SET);")
				output.append("fseek(file" + str(linenum) + ", " + str(splitline[4]) + " , SEEK_SET);")
			else:
				output.append("file" + str(linenum) + " = fopen(\"" + str(splitline[2]) + "\", \"a\");")
			output.append("fputc(" + str(varout) + " , file" + str(linenum) + ");")
			output.append("fclose(file" + str(linenum) + ");")	
		
		if splitline[0] == "FILEIN":
			output.append("FILE *file" + str(linenum) + " = NULL;")
			output.append("file" + str(linenum) + " = fopen(\"" + str(splitline[2]) + "\", \"r\");")
			if len(splitline) > 3 and splitline[3] == "AT":
				if len(splitline) > 4 and splitline[4] in varnames:
					output.append("fseek(file" + str(linenum) + ", " + str(splitline[4]) + ".extdata[0] , SEEK_SET);")
				output.append("fseek(file" + str(linenum) + ", " + str(splitline[4]) + " , SEEK_SET);")
			output.append(str(splitline[1]) + ".extdata[0] = fgetc(file" + str(linenum) + ");")
			output.append("fclose(file" + str(linenum) + ");")
		
		if splitline[0] == "FILESIZE":
			output.append("FILE *file" + str(linenum) + " = NULL;")
			output.append("file" + str(linenum) + " = fopen(\"" + str(splitline[2]) + "\", \"r\");")
			output.append("fseek(file" + str(linenum) + ", 0L, SEEK_END);")
			output.append(str(splitline[1]) + ".extdata[0] = ftell(file" + str(linenum) + ");")
			output.append("fclose(file" + str(linenum) + ");")
			
		
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
