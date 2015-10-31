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

#format: VARNAME SIZE SIGN
variables = []

varnames = []
vartypes = ["BINARY", "HEX", "CHAR"]
varsizes = []
varvals = []
varstofree = []

#flags
hasstart = 0
hasend = 0
multicomment = 0


#Checks if a comment exists on the line
#Takes: a line from readlines()
#Returns: 1 if a comment is found, 0 otherwise
def checkComment(line):
	global multicomment
	continueBool = 0
	if len(line) > 1 and (line.find("#/") != -1):
		multicomment = 0
		continueBool = 1
	
	elif multicomment == 1:
		continueBool = 1	
		
	elif len(line.strip()) > 1 and line.strip()[0] == "/" and line.strip()[1] == "#":
		multicomment = 1
		continueBool = 1

	elif len(line.strip()) > 0 and line.strip()[0] == "#":
		continueBool = 1
	return continueBool

#Checks if line contains start or end
#Takes: a line
def startEnd(line):
	global hasstart
	global hasend
	
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
	
	
#Checks if a line is asm or passthroc, if it is put it directly into c as is
#Takes: a splitline
#Returns: 1 if asm or passthroc is found, 0 otherwise 
def asm_passthroc(splitline):
	cont = 0
	if splitline[0] == "ASM" or splitline[0] == "PASSTHROC":
		del splitline[0]
		newline = ""
		for i in splitline:
			newline += i
			newline += " "
		output.append(newline)
		cont = 1
		
	return cont


#Converts a decimal number to a binary value 
#Takes the variable name, the length as number of nibbles and the value that is being turned into binary
def convert2bin(var ,size, value):
	cnt = 0 #Attempting stuff here
	binval = bin(int(value))
	binval = binval[2:]
	lenbin = len(binval)
	temp = ""
	while cnt < int(size):
		temp = temp + "0000"
		cnt += 1
	cnt = 0
	temp = temp[:-lenbin]
	temp = temp + binval
	binval = temp
	lenbin = len(binval)
	
	while cnt < int(size):
		a = cnt*4
		b = cnt*4 + 4
		num = int(binval[a:b],2)
		output.append(var + "["+str(cnt)+"].data = " + str(num) + ";")
		cnt += 1

#Converts an integer to hex values in C and assigns them to the passed in variable
#Takes variable name, size of variable, name of c variable so it isnt repeated, and linennum
def convert2binC(var, size, cvar, linenum):
	linenum = str(linenum)
	#output.append("char buffer"+linenum+"["+str(size)+"];")
	output.append("char * buffer"+linenum+" = malloc(snprintf(NULL, 0, \"%X\", "+cvar+") + 1);")

	#output.append("printf(\"%d\\n\", "+cvar+");")
	output.append("sprintf(buffer"+linenum+", \"%X\", "+cvar+");")
	#output.append("printf(\"%s\\n\\n\", buffer"+linenum+");")
	output.append("int temp"+linenum+";")
	cnt = 0
	
	while cnt < size:
		output.append(var+"["+str(cnt)+"].data = 0;")
		cnt += 1

	#cnt = size - 1
	#bufcnt = 0
	#while cnt >= 0:
	output.append("int flag"+linenum+" = 0;")
	output.append("int tempcount"+linenum+" = "+str(size - 1)+";")
	output.append("int bufcount"+linenum+" = "+str(size-1)+";")
	output.append("while(tempcount"+linenum+" >= 0){")
	#output.append("printf(\"%d\\n\", buffer"+linenum+"[bufcount"+linenum+"] - '0');")
	output.append("temp"+linenum+" = buffer"+linenum+"[bufcount"+linenum+"] - '0';")
	#output.append("printf(\"%d\\n\", temp"+linenum+");")

	output.append("if (temp"+linenum+" >= 0 && temp"+linenum+" <=22){")
	output.append("if (temp"+linenum+" > 16){")
	output.append("temp"+linenum+" = temp"+linenum+" - 7;")
	output.append("}")
	output.append(var + "[tempcount"+linenum+"].data = temp"+linenum+";")
	output.append("bufcount"+linenum+"--;")
	output.append("tempcount"+linenum+"--;")
	output.append("flag"+linenum+" = 1;")
	output.append("}")
	output.append("else{")
	output.append("if(flag"+linenum+" == 1){")
	output.append("break;")
	output.append("}")
	output.append("bufcount"+linenum+"--;")
	output.append("}")
	output.append("}")
	output.append("free(buffer"+linenum+");")


#Checks the nibble length of the variable
#Takes name of variable
#Returns length of variable 
def varLength(varname):
	index = varnames.index(varname)
	#print varname
	length = varsizes[index]
	return length
	

#Takes a series of values between 0 and 15 and adds them together in C
#Takes name of variable holding values, name of new c value created
def hex2int(varname, cvar):
		length1 = int(varLength(varname))
		cnt = length1 - 1
		cnt2 = 0
		output.append("int "+cvar+" = 0;")
		while cnt >= 0:
			output.append(cvar+" = "+cvar+" + ("+varname+"["+str(cnt)+"].data * (pow(16.0,  "+str(cnt2)+"))) ;")
			cnt -= 1
			cnt2 += 1
		#output.append("printf(\"%d\\n\", "+cvar+");")


	
#Checks if variable declaration is being performed
#Takes: a splitline
def variableDeclaration(splitline):
	if splitline[0] == "LET":
		for i in varnames:
			if len(splitline) > 1 and i == splitline[1]:
				print "Variable name " + splitline[1] + " already declared!"
				quit(1)
		# The variable name will be the second whitespace delimited field
		varnames.append(splitline[1])
		
		if len(splitline) > 2 and splitline[2] == "AS":
			# Firstly, check if we're using SIGNED or UNSIGNED - if neither, UNSIGNED.
			if len(splitline) <= 6 or splitline[6] == "UNSIGNED":
				output.append("nib *" + splitline[1] + " = malloc(sizeof(nib) * " + splitline[3] + ");")
				varsizes.append(int(splitline[3]))
				varstofree.append(splitline[1])
			elif len(splitline) > 6 and splitline[6] == "SIGNED":
				output.append("snib *" + splitline[1] + " = malloc(sizeof(snib) * " + splitline[3] + ");")
				varsizes.append(int(splitline[3]))
				varstofree.append(splitline[1])
				
			if len(splitline) > 4 and splitline[4] == "BE":
				convert2bin(splitline[1],splitline[3],splitline[5])
				#output.append(splitline[1] + "[0].data = " + splitline[5] + ";")
			
		else:
			output.append("nib *" + splitline[1] + " = malloc(sizeof(nib));")
			varsizes.append(1)
			if len(splitline) > 2 and splitline[2] == "BE":
				output.append(splitline[1] + "[0].data = " + splitline[3] + ";")

#TODO this probably broke
#Checks which vartype is being used, removes the unnecarry word and performs required update to line
#Takes: A splitline
#Returns: The updated splitline
def checkVartype(splitline, index):
	vartype = splitline[index]
	splitline.remove(splitline[index])
	if vartype == "BINARY":
		splitline[index] = "0b" + splitline[index]
	elif vartype == "HEX":
		splitline[index] = "0x" + splitline[index]
	elif vartype[index] == "CHAR":
		splitline[index] = "\'" + splitline[index] + "\'"
	return splitline


#Checks if unary math operations are being performed with assignments as the first thing on the line
#Takes: a splitline
def unarymath(splitline, linenum):	
	if ((splitline[0] in varnames) and (splitline[2] in ["COMPLEMENT", "NEGATE", "INCREMENT", "DECREMENT", "NOT", "ADDRESSOF", "CONTENTOF"])): 
	#unary operations
		indexright = 0
		indexleft = 0
		
		length = varLength(splitline[0])
		cvar = "var" + str(linenum)
		hex2int(splitline[0], cvar)
		cvar2 = "varr" + str(linenum)

		if splitline[1] == "AT":
			indexright = int(splitline[2])
			del splitline[1]
			del splitline[1]
		if len(splitline) > 3 and splitline[3] == "AT":
			indexleft = int(splitline[4])
			del splitline[3]
			del splitline[3]

		if splitline[3] in vartypes:
			splitline = checkVartype(splitline, 3)
			
		elif splitline[3] in varnames:
			hex2int(splitline[3],cvar2)
			#splitline[3] = splitline[3] + "[" + str(indexleft) + "].data"
			
		#splitline[0] += "[" + str(indexright) + "]"
		#unary math/bit/logic operators
		if splitline[2] == "COMPLEMENT":
			output.append(cvar +" = ~"+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + ".data = ~" + splitline[3] + ";")
		elif splitline[2] == "NEGATE":
			output.append(cvar +" = -"+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + ".data = -" + splitline[3] + ";")
		elif splitline[2] == "INCREMENT":
			output.append(cvar +" = "+cvar2+" + 1;")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + ".data = " + splitline[3] + " + 1;")
		elif splitline[2] == "DECREMENT":
			output.append(cvar +" = "+cvar2+" - 1;")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + ".data = " + splitline[3] + " - 1;")
		elif splitline[2] == "NOT":
			output.append(cvar +" = !"+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + ".data = !" + splitline[3] + ";")
		elif splitline[2] == "ADDRESSOF":
			output.append(cvar +" = &("+cvar2+");")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + ".data = &(" + splitline[3] + ");")
		elif splitline[2] == "CONTENTOF":
			output.append(cvar +" = *("+cvar2+");")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + ".data = *(" + splitline[3] + ");")
	

#Checks if binary math operations are being performed with assignments as the first thing on the line
#Takes: a splitline, linenumber
def binarymath(splitline, linenum):					
	if ((splitline[0] in varnames) and len(splitline) > 4): 
	
		binopindexright = 0			
		binopindexleft = 0	
		
		length = varLength(splitline[0])
		cvar = "var" + str(linenum)
		hex2int(splitline[0], cvar)
		cvar2 = "varr" + str(linenum)

			
	
		if splitline[2] in vartypes:
			splitline = checkVartype(splitline, 2)

		else:
			if len(splitline) > 3 and splitline[3] == "AT":
				binopindexright = int(splitline[3])
				del splitline[3:4]
			if splitline[2] in varnames:
				length2 = varLength(splitline[2])
				#splitline[2] = splitline[2] + "[" + str(binopindexright) + "].data"
			
		if len(splitline) > 4:
			if splitline[4] in vartypes:
				splitline = checkVartype(splitline, 4)
			else:
				if len(splitline) > 5 and splitline[5] == "AT":
					binopindexright = int(splitline[6])
					del splitline[5:6]
				if splitline[4] in varnames:
					hex2int(splitline[4],cvar2)
					#splitline[4] = splitline[4] + "[" + str(binopindexleft) + "].data"
				else:
					output.append("int "+cvar2+" = "+splitline[4]+";")

		if splitline[3] == "ADD":
			output.append(cvar +" = "+cvar+" + "+cvar2+";")
			#output.append("printf(\"%d\\n\", "+cvar+");")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " + " + splitline[4] + " ;")
		elif splitline[3] == "SUBTRACT":
			output.append(cvar +" = "+cvar+" - "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " - " + splitline[4] + " ;")
		elif splitline[3] == "MULTIPLY":
			output.append(cvar +" = "+cvar+" * "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " * " + splitline[4] + " ;")
		elif splitline[3] == "DIVIDE":
			output.append(cvar +" = "+cvar+" / "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " / " + splitline[4] + " ;")
		elif splitline[3] == "MODULUS":
			output.append(cvar +" = "+cvar+" % "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " % " + splitline[4] + " ;")
	
		#binary bitwise operators
		elif splitline[3] == "AND":
			output.append(cvar +" = "+cvar+" & "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " & " + splitline[4] + " ;")
		elif splitline[3] == "NAND":
			output.append(cvar +" = ~("+cvar+" & "+cvar2+");")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = ~(" + splitline[2] + " & " + splitline[4] + ") ;")
		elif splitline[3] == "OR":
			output.append(cvar +" = "+cvar+" | "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " | " + splitline[4] + " ;")
		elif splitline[3] == "NOR":
			output.append(cvar +" = ~("+cvar+" | "+cvar2+");")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = ~(" + splitline[2] + " | " + splitline[4] + ") ;")
		elif splitline[3] == "XOR":
			output.append(cvar +" = "+cvar+" ^ "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " ^ " + splitline[4] + ";")
		elif splitline[3] == "XNOR":
			output.append(cvar +" = ~("+cvar+" ^ "+cvar2+");")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = ~(" + splitline[2] + " ^ " + splitline[4] + ") ;")
		
		#binary bitshifting
		elif (splitline[3] == "RROTATE" or splitline[3] == "RSHIFT"):
			output.append(cvar +" = "+cvar+" >> "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " >> " + splitline[4] + ";")
		elif (splitline[3] == "LROTATE" or splitline[3] == "LSHIFT"):
			output.append(cvar +" = "+cvar+" << "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " << " + splitline[4] + ";")
		
		#binary logical operators
		elif splitline[3] == "ALSO":
			output.append(cvar +" = "+cvar+" && "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " && " + splitline[4] + ";")
		elif splitline[3] == "EITHER":
			output.append(cvar +" = "+cvar+" || "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " || " + splitline[4] + ";")
		
		#Logical tests
		elif splitline[3] == "EQUALS":
			output.append(cvar +" = "+cvar+" == "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " == " + splitline[4] + ";")
		elif splitline[3] == "NOTEQUALS":
			output.append(cvar +" = "+cvar+" != "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " != " + splitline[4] + ";")
		elif splitline[3] == "GREATER":
			output.append(cvar +" = "+cvar+" > "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " > " + splitline[4] + ";")
		elif splitline[3] == "GREATEREQUALS":
			output.append(cvar +" = "+cvar+" >= "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " >= " + splitline[4] + ";")
		elif splitline[3] == "LESS":
			output.append(cvar +" = "+cvar+" < "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " < " + splitline[4] + ";")
		elif splitline[3] == "LESSEQUALS":
			output.append(cvar +" = "+cvar+" <= "+cvar2+";")
			convert2binC(splitline[0], length, cvar, linenum)
			#output.append(splitline[0] + "[0].data = " + splitline[2] + " <= " + splitline[4] + ";")


#Checks if assigning a variable to another variable
#Takes: a splitline
def assignment(splitline):					
	if ((splitline[0] in varnames) and (len(splitline) == 3)):
		length = varLength(splitline[0])
		
		#If assigning a variable to antoehr variable
		if(splitline[2] in varnames):
			length1 = varLength(splitline[0])
			length2 = varLength(splitline[2])
			length = min(length1, length2)
			cnt = 0
			
			#Set the value back to zero so that it doesnt accidently be wrong
			while cnt < length1:
				output.append(splitline[0]+"["+str(cnt)+"].data = 0;")
				cnt += 1
			cnt = 0
			
			#Set the 1st var to the value of the 2nd var
			while cnt < length:
				output.append(splitline[0] + "["+str(length1 - cnt - 1)+"].data = " + splitline[2] + "["+str(length2 - cnt - 1)+"].data;")
				cnt += 1
		#assigning a value to a variable
		else:
			convert2bin(splitline[0], length, splitline[2])
			#output.append(splitline[0] + "[0].data = " + splitline[2] + ";")

#Checks a line for any conditionals
#Takes: a splitline, linenum
def conditionals(splitline, linenum):
	if(splitline[0] in ["IF", "ELSEIF", "ELSE", "ENDIF", "LOOPWHILE", "ENDLOOP", "LOOPAGAIN", "EXITLOOP", "EXITIF", "EARLYEND"]):
		
		
		vartype = ""
		boolindex = 0
		if len(splitline) > 1 and splitline[1] in vartypes:
			splitline = checkVartype(splitline, 1)
		elif len(splitline) > 2 and splitline[2] == "AT":
			boolindex = int(splitline[3])
		if len(splitline) > 1:
			splitline[1] = splitline[1] + "[" + str(boolindex) + "].data"

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
	
		#Earlyend
		elif splitline[0] == "EARLYEND":
			output.append("goto END;")


#goto and labels
#Takes: splitline
def goto(splitline):
	if(splitline[0] in ["GOTO", "LABEL"]):
		if splitline[0] == "LABEL":
			output.append(splitline[1] + ":")
		elif splitline[0] == "GOTO":
			output.append("goto " + splitline[1] + ";")

#Checks if the line contains any function properties
#Takes: splitline
def functionProperties(splitline):
	if splitline[0] == "FUNCTION":
		#must match declaration sig
		nextparam = 0
		temp = ""
		if len(splitline) > 3 and splitline[2] == "RETURNS":
			temp += "nib * " + splitline[1]  + "("
			nextparam = 4
		else:
			temp += "void " + splitline[1] + "("
			nextparam = 2
		while len(splitline) >= nextparam + 1:
			#print len(splitline)
			if splitline[nextparam] != "TAKES" and splitline[nextparam] != "ASWELL":
				nextparam = nextparam + 1
				continue
			temp += "nib *" + splitline[nextparam + 1] + " " 
			nextparam += 2
			if len(splitline) >= nextparam + 1:
				temp += ","
		temp2 = temp
		temp2 += ");"
		functionindex = output.index("/*Function declarations go here*/")
		output.insert(functionindex + 1, temp2)
		
		temp += "){"
		output.append(temp)
	elif splitline[0] == "ENDFUNCTION":
		output.append("}")
	elif splitline[0] == "RETURN":
		output.append("return " + splitline[1] +";")


#Performs the getchar function
#Takes: splitline, current linenumber
def getchar(splitline, linenum):
	#assume we're starting at index 0, unless told otherwise
	startindex = 0
	secondindex = 0
	fornum = 1
	readlocation = "stdin"
	
	#this is how they can tell us otherwise
	if len(splitline) > 3 and splitline[3] == "AT":
		startindex = int(splitline[4]) * 2
		splitline.remove(splitline[3])
		splitline.remove(splitline[3])
	
	#find the index of where to start to read from the file
	if len(splitline) > 4 and splitline[4] == "AT":
		secondindex = int(splitline[5])
		splitline.remove(splitline[4])
		splitline.remove(splitline[4])
		
	#Check how many chars we should read in
	if len(splitline) > 5 and splitline[4] == "FOR":
		fornum = int(splitline[5])
		splitline.remove(splitline[4])
		splitline.remove(splitline[4])

	elif len(splitline) > 4 and splitline[3] == "FOR":
		fornum = int(splitline[4])
		splitline.remove(splitline[3])
		splitline.remove(splitline[3])

		
	if len(splitline) > 3 and splitline[3]:
		readlocation = splitline[3]
		
	#output.append(splitline[1] + ".extdata[0] = getchar();")
	if readlocation != "stdin":
		output.append("FILE *file" + str(linenum) + "= fopen(\"" + readlocation + "\", \"r\");")
		readlocation = "file" + str(linenum)
	
	output.append("char tempc" + str(linenum)+ "[" + str(fornum) + "]; ")#= getc(" + readlocation + ");")
	
	counter = 0	
	
	#Check which index to begin reading from file
	if secondindex != 0:
		output.append("fseek( " + readlocation + ", " + str(secondindex) + ", SEEK_SET );")
	
	while(counter < fornum):	
		output.append("tempc" + str(linenum) + "[" + str(counter) + "] = getc(" + readlocation + ");")
		output.append(splitline[2] + "[" + str(startindex) + "].data = tempc" + str(linenum) + "[" + str(counter) + "]" + ";")
		output.append(splitline[2] + "[" + str(int(startindex) + 1) + "].data = tempc" + str(linenum) + "[" + str(counter) + "]" + " >> 4;")
		counter = counter + 1
		startindex = startindex + 2
	
	if readlocation != "stdin":
		output.append("fclose(file" + str(linenum) + ");")	
	

#Performs the putchar function
#Takes: splitline, and current linenumber
def putchar(splitline, linenum):	
	#assume we're starting at index 0, unless told otherwise
	startindex = 0
	secondindex = 0
	fornum = 1
	writelocation = "stdout"
	
	#this is how they can tell us otherwise
	if len(splitline) > 3 and splitline[3] == "AT":
		startindex = int(splitline[4]) * 2
		splitline.remove(splitline[3])
		splitline.remove(splitline[3])
		
	#find the second index if available	
	if len(splitline) > 4 and splitline[4] == "AT":
		secondindex = int(splitline[5])
		splitline.remove(splitline[4])
		splitline.remove(splitline[4])
		
	#Check how many chars we should read in
	if len(splitline) > 5 and splitline[4] == "FOR":
		fornum = int(splitline[5])
		splitline.remove(splitline[4])
		splitline.remove(splitline[4])

	elif len(splitline) > 4 and splitline[3] == "FOR":
		fornum = int(splitline[4])
		splitline.remove(splitline[3])
		splitline.remove(splitline[3])
		
	if len(splitline) > 3:
		writelocation = splitline[3]
	

	
	if writelocation != "stdout":
		buffer1 = 0
		#If the user wants to putc chars into the middle of the file - get length of file, save current file in buffer, print buffer into file up to index, putc, then put rest of buffer into file
		if secondindex != 0:
			buffer1 = 1
			output.append("FILE *file" + str(linenum) + "= fopen(\"" + writelocation + "\", \"r+\");")
			filename = writelocation
			writelocation = "file" + str(linenum)
			#output.append("fseek("+ writelocation + ", "+ str(secondindex) +", SEEK_SET);") This performs overwrite if you comment out rest of block below here
			output.append("fseek("+ writelocation + ", 0, SEEK_END);")
			output.append("long size"+str(linenum)+" = ftell(" + writelocation + ");")
			output.append("fseek("+ writelocation + ", 0, SEEK_SET);")
			output.append("char * buffer"+str(linenum)+" = (char*) malloc (sizeof(char)*size"+str(linenum)+");")
			output.append("fread (buffer"+str(linenum)+",sizeof(char),size"+str(linenum)+"," + writelocation + ");")
			output.append("freopen(\"" + filename + "\", \"w\", file" + str(linenum) + ");")
			output.append("fwrite(buffer"+str(linenum)+", sizeof(char),"+ str(secondindex) +","+ writelocation +" );")
			#output.append("printf(\"%ld\\n\", size);")
			#output.append("printf(\"%s\\n\", buffer);")
			
		if buffer1 == 0:
			output.append("FILE *file" + str(linenum) + "= fopen(\"" + writelocation + "\", \"a\");")
			writelocation = "file" + str(linenum)

	counter = 0
	output.append("char ch" + str(linenum) + " = 0;")
	
	
	while(counter < fornum):
		output.append("ch" + str(linenum) + " = 0;")
		output.append("ch" + str(linenum) + " = (ch" + str(linenum) + " & 0xF0) | (" + str(splitline[2]) + "[" + str(startindex) + "].data & 0xF);")
		output.append("ch" + str(linenum) + " = (ch" + str(linenum) + " & 0x0F) | ((" + str(splitline[2]) + "[" + str(int(startindex) + 1) + "].data & 0xF) << 4);")
	
		output.append("putc(ch" + str(linenum) + ", " + writelocation + ");")
		
		counter = counter + 1
		startindex = startindex + 2
	
	if writelocation != "stdout":		
		if buffer1 == 1:
			output.append("fwrite(buffer"+str(linenum)+"+"+str(secondindex)+", sizeof(char), size"+str(linenum)+"-"+str(secondindex)+", "+ writelocation +");")
			#output.append("fwrite(buffer+"+str(secondindex)+", sizeof(char), sizeof(buffer)-"+str(secondindex)+", "+ writelocation +");")
			output.append("free(buffer"+str(linenum)+");")
		output.append("fclose(file" + str(linenum) + ");")
	
#Checks for and performs function calls
#Takes: splitline, current line number
def functionCall(splitline, linenum):
	if splitline[0] == "CALL":
		temp = ""
		if splitline[1] == "GETCHAR":
			getchar(splitline, linenum)
		elif splitline[1] == "PUTCHAR":
			putchar(splitline, linenum)
		else:	
			if len(splitline) > 3 and splitline[2] == "RETURNS":
				temp += splitline[3] + " = "
				nextparam = 5
			else:
				nextparam = 2
			
			temp += splitline[1] + "( "
			while len(splitline) > nextparam:
				temp += splitline[nextparam]
				if len(splitline) >= nextparam + 2:
					temp += ", "
				nextparam += 2
			temp += ");"
			output.append(temp)


#Checks for filein/out or size
#Takes: splitline, linenum
def files(splitline, linenum):
	if splitline[0] in ["FILEIN", "FILEOUT", "FILESIZE"]:
		var = splitline[1]
		filename = splitline[2]
		
		if splitline[0] == "FILEIN":
			pass
			
		elif splitline[0] == "FILEOUT":
			pass
		
		#Checks for the size of a file in bits (Needs two nibbles to store value)
		elif splitline[0] == "FILESIZE":
			output.append("FILE *file" + str(linenum) + "= fopen(\"" + filename + "\", \"r\");")
			readlocation = "file" + str(linenum)
			output.append("fseek("+ readlocation + ", 0L, SEEK_END);")
			output.append(var + "[0].data = ftell(" + readlocation + ");")
			output.append(var + "[1].data = ftell(" + readlocation + ") >> 4;")


def main():
	
	if len(sys.argv) < 2:
		print 'No file specified'
		quit()
	inputf = open(sys.argv[1])
	linenum = 1
	# Flags for program START and END - one per program


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
	
	output.append("typedef struct _snib")
	output.append("{")
	output.append("int8_t data : 4;")
	output.append("} snib;")
	
	output.append("/*Function declarations go here*/")
	output.append("/*Function declarations go here*/")
	output.append("")
	output.append("")

	for line in inputf.readlines():
		#Check for comments
		continueBool = checkComment(line)
		if continueBool == 1:
			continue
		
		#Check for Start/End
		startEnd(line)
		
		splitline = line.split()
		
		#Empty line
		if len(splitline) == 0:
			continue
		
		#Check for asm or passthroc
		continueBool = asm_passthroc(splitline)
		if continueBool == 1:
			continue
		
		#Check for variable declaration
		variableDeclaration(splitline)
		
		#Check for unary math being performed
		unarymath(splitline, linenum)
		
		#Check for binary math being performed
		binarymath(splitline, linenum)
		
		#Check for assignment
		assignment(splitline)
		
		#Check for conditionals
		conditionals(splitline,linenum)
		
		#Check for goto/labels
		goto(splitline)

		#Check for functions
		functionProperties(splitline)
		
		#Check for function call
		functionCall(splitline, linenum)
		
		#Check for file I/Os
		files(splitline,linenum)
		
		#Check for NOHEADER
		if splitline[0] == "NOHEADER":
			output.remove("puts(HEADER);")
			output.remove("puts(\"\");")
		
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
	
	
	# This if only runs if this file is called as a script - if it is included, it doesn't
if __name__ == "__main__":
	main()
