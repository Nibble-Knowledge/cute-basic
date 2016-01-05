#!/usr/bin/python
import sys
import os

#stack for keeping track of IF statements - holds line numbers of IF
ifStatementStack = []
endifStack = []
#stack for keeping track of LOOPWHILE statements - holds like numbers of LOOPWHILE
loopStatementStack = []
#giant buffer holding output
output = []
data = []
#list of names of variables

#format: VARNAME SIZE SIGN
variables = []

varnames = []
varsizes = []
varvals = []

funcnames = []
funcstack = []
returns = 0

signed = []
files = []

funcVars = []

baseaddress = -1

identifiers = ["START" , "END", "SIGNED", "LET", "BE", "AS", "COMPLEMENT", "NEGATE", "INCREMENT", "DECREMENT", 
"NOT", "ADDRESSOF", "CONTENTOF", "IF", "ELSEIF", "ELSE", "ENDIF", "LOOPWHILE", "ENDLOOP", "LOOPAGAIN", "EXITLOOP", 
"EXITIF", "EARLYEND", "LABEL", "GOTO", "ADD", "SUBTRACT", "MODULUS", "MULTIPLY", "DIVIDE", "ALSO", "EITHER", "AND", 
"OR", "XOR", "NAND", "NOR", "XNOR", "LSHIFT", "RSHIFT", "LROTATE", "RROTATE", "ADDRESSOF", "CONTENTOF", "FUNCTION", 
"ENDFUNCTION", "RETURN", "RETURNS", "TAKES", "ASWELL"]


#Added by Naomi to allow specific static pointers to be used
validPointers = ["*CHIP_SELECT", "*STATUS_BUS", "*DATA_BUS"]

#flags
hasstart = 0
hasend = 0
multicomment = 0
asmFunc = 0



#Checks the nibble length of the variable
#Takes name of variable
#Returns length of variable 
def varLength(varname):
	if varname in varnames:
		index = varnames.index(varname)
		
		if(len(varsizes) > index):
			length = varsizes[index]
		#Assuming literals should be 4?
		else:
		#if length == None:
			length = 4
		return int(length)
	

#Check the length of two lines and return the difference between them (-# means var 1 is smaller by # nibs, 0 means even, +# means var 1 is bigger by # nibs)	
#Takes 2 variables
#Returns an integer (differnece in size)
def compareLength(varname1, varname2):
	if(varname1 in varnames and varname2 in varnames):
		length1 = varLength(varname1)
		length2 = varLength(varname2)
		return length1 - length2
		
#Takes two variables
#Returns the length of the longer variable
def longer(var1, var2):
	longer = varLength(var1)
	if longer == None:
		longer = 4
		
	longer2 = varLength(var2)
	if longer2 == None:
		longer2 = 4
		
	if longer < longer2:
		longer = longer2
	return longer
		
#Checks if a value is a variable or literal, and adds the N_[] if its a literal
#Takes a potential variable
#Returns the same var, or an encased literal
def literal(var):
	if var not in varnames:
		var = "N_[" + var + "]"
	return var
	
#Writes the ASM code needed to perform signed or unsigned extension depending on variable 
#Takes a variable and a size to extend to 
#Returns the extended value label
def extend(var, difference):
	#Number of nibbles needed to extend by 
	size = int(difference)
	cnt = 0
	length = varLength(var)
	total = length + difference
	#Sign extend
	if var in signed:
		extendedVar = var + str(total*4) + "signed"
		if(extendedVar not in varnames):
			data.append(var + str(total) + "signed: .data " + str(total) + " 0")
			varnames.append(extendedVar)
			

		
		op = multinibOp(length, "MOV")
		output.append(op +  " " + var + " INTO " + extendedVar + "[" + str((total - length )) + "]")
		
		#TODO Not sure if im using signex right
		output.append("LOD " + var)
		output.append("SIGNEX ACC")
			
		#output.append(op + " ") Just taking this out for now, it messes up stuff.

	#Unsigned extend	
	else:
		extendedVar = var + str(total) + "unsigned"
		if(extendedVar not in varnames):
			data.append(var + str(total) + "unsigned: .data " + str(total) + " 0")
			varnames.append(extendedVar)

		op = multinibOp(length, "MOV")
		output.append(op +  " " + var + " INTO " + extendedVar  + "[" + str((total - length )) + "]")
	
		output.append("LOD N_[0]")
	
	#Fill the remaining values with the extended value	

	#Wrong endianness
	#cnt = 0
	#while cnt < size:
	
	cnt = size - 1 
	while cnt >= 0:
		output.append("STR "+ extendedVar + "[" + str(cnt) + "]")
		cnt -= 1

	return extendedVar

#Takes an operation and a size and returns the oepration with that size included
def multinibOp(length, op):
	if str(length) == "1":
		return op
	else:
		return op + str(int(length)*4)
	
	
#Checks if we are in a function, if we are change all labels to be the local version of the label
#Takes the splitline
#Returns: the unaltered splitline or the splitline with function names appended
def localVars(splitline):
	if len(funcstack) > 0:
		cnt = 0
		#Check each word in splitline
		for word in splitline:
			num = word.isdigit()
			#If word is not an identifier or a number it is a label - therefore add funcname_ before it 
			if word not in identifiers and num == False:
				splitline[cnt] = funcstack[-1] + "_" + word
			cnt += 1
	return splitline



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
	cont = 0
	global hasstart
	global hasend
	
	if line.strip() == "START":
		if hasstart == 1:
			print "START already declared"
			exit(1)
		else:
			hasstart = 1
			output.append("START:")

		cont = 1
			
	elif line.strip() == "END":
		if hasend == 1:
			print "END already declared"
			exit(1)
		else:
			hasend = 1
			output.append("END:")
		cont = 1
	return cont

		
#Checks if a line is asm or passthroc, if it is put it directly into output as is
#Takes: a splitline
#Returns: 1 if asm or passthroc is found, 0 otherwise 
def asm_passthroc(splitline, linenum):
	global asmFunc
	cont = 0
	if splitline[0] == "ASM" or splitline[0] == "PASSTHROC" or asmFunc == 1:
		#If its a special variable function type
		if (len(splitline) > 1 and splitline[1] == "FUNCTION") or asmFunc == 1:
			asmFunction(splitline, linenum)
		else:	
			del splitline[0]
			newline = ""
			for i in splitline:
				newline += i
				newline += " "
			output.append(newline)
		cont = 1
		
	return cont	


#Checks if variable declaration is being performed
#Takes: a splitline
def variableDeclaration(splitline, linenum):
	cont = 0
	if splitline[0] == "LET":
		#LET VAR - this should default a size and value
		#LET VAR AS SIZE- this should default a value
		#LET VAR BE VAL (SIGNED)- this should default a size, and if no signed default unsigned
		#LET VAR AS SIZE BE VAL (SIGNED) - if no signed, default unsigned
		
		if splitline[1] in identifiers:
			print "Error line " + str(linenum) + ": can not use identifier " + splitline[1] + " as a variable name"


		#Disallow variable names starting with '*' unless we have them in our pointer list (at top of file)
		#Also, don't allow pointers to have non-default size, or any initialisation value.
		if splitline[1][0] == '*' and (splitline[1] not in validPointers or len(splitline) > 2):
			print "Error line " + str(linenum) + ": special character * can only be used with valid static labels"
		
		#Check if variable already exists
		for i in varnames:
			if (len(splitline) > 1 and i == splitline[1] ):
				if(len(funcstack) > 0 and funcstack[-1] + "_" + splitline[1] not in varnames):
					a = 0 #do nothing
				else:
					print "Error line " + str(linenum) + ": Variable name " + splitline[1] + " already declared!"
					quit(1)
				
		
		# The variable name will be the second whitespace delimited field
		varnames.append(splitline[1])
		temp = ''
		temp += splitline[1]
		
		defaultSize = 4 #4 nibble default
		defaultVal = 0
		
		#LET VAR
		if len(splitline) == 2:
			temp +=": .data " + str(defaultSize) + " " + str(defaultVal)
			varsizes.append(defaultSize)

		#LET VAR AS or LET VAR AS BE
		elif splitline[2] == "AS":
			#LET VAR AS
			#Check that valid nib size
			if (splitline[3] not in ["1", "2", "4", "8", "16"]):
				print "Error on line: " + str(linenum) + ": Invalid size in nibbles, size must be 1, 2, 4, 8 or 16"
				exit(1)
				
			if len(splitline) == 4:
				temp += ": .data " + splitline[3] + " " + str(defaultVal)
				varsizes.append(splitline[3])

			#LET VAR AS BE	
			else:
				if(len(splitline) > 5 and splitline[5][0] == "\""):
					temp += ": .ascii " + splitline[5]
					varsizes.append(splitline[3])
				else:
					temp += ": .data " + splitline[3] + " " + splitline[5]
					varsizes.append(splitline[3])
				
		#LET VAR BE
		elif splitline[2] == "BE":
			if(splitline[3][0] == "\""):
				temp += ": .ascii " + splitline[3]
				varsizes.append(len(splitline[3]) * 8) #TODO not sure if this value is correct
			else:
				temp += ": .data " + str(defaultSize) + " " + splitline[3]
				varsizes.append(defaultSize)
			
		#Invalid input	
		else:
			print "Error on line " + str(linenum) + ": Invalid variable declaration " +  str(splitline)
			exit(1)
		#If last input is signed	#TODO figure out what this should do
		if splitline[-1] == "SIGNED":
			signed.append(splitline[1])
			
		#Add the data declaration - unless it's a pointer!
		if (splitline[1] not in validPointers):	
			data.append(temp)
		cont = 1
	return cont

#Checks if unary math operations are being performed with assignments as the first thing on the line
#Takes: a splitline
def unarymath(splitline, linenum):	
	cont = 0
	if (len(splitline) > 3 and (splitline[0] in varnames) and (splitline[2] in ["COMPLEMENT", "NEGATE", "INCREMENT", "DECREMENT", "NOT", "ADDRESSOF", "CONTENTOF"])): 
		length = longer(splitline[2], 0)	
		
		
	
		#unary math/bit/logic operators
		if splitline[2] == "COMPLEMENT":
			if length == 4:
				output.append("NOT " + splitline[3] + " INTO " + splitline[0])
			else:
				output.append("NOT" + str(length) + " " + splitline[3] + " INTO " + splitline[0])
				
		elif splitline[2] == "NEGATE":
			if length == 4:
				output.append("NEG " + splitline[3] + " INTO " + splitline[0])
			else:
				output.append("NEG" + str(length) + " " + splitline[3] + " INTO " + splitline[0])
				
		elif splitline[2] == "INCREMENT":
			if length == 4:
				output.append("INC " + splitline[3] + " INTO " + splitline[0])
			else:
				output.append("INC" + str(length) + " " + splitline[3] + " INTO " + splitline[0])
				
		elif splitline[2] == "DECREMENT":
			if length == 4:
				output.append("SUB " + splitline[3] + " N_[1] INTO " + splitline[0])
			else:
				output.append("SUB" + str(length) + " " + splitline[3] + " N_[1] INTO " + splitline[0])

			
		elif splitline[2] == "NOT":
			output.append("LOGNOT ACC")
			output.append("MOV " + splitline[3] + " INTO " + splitline[0])
			#TODO Dont think this is right but have to double check - only accumualtor lognot?
			
		elif splitline[2] == "ADDRESSOF":
			output.append("MOVADDR "+ splitline[3] +" INTO " + splitline[0])
			#TODO not sure if these parts are right
		elif splitline[2] == "CONTENTOF":
			if length == 4:
				output.append("MOV " + splitline[3] + " INTO " + splitline[0])
			else:
				output.append("MOV" + str(length) + " " + splitline[3] + " INTO " + splitline[0])
		cont = 1
	return cont

#Checks if binary math operations are being performed with assignments as the first thing on the line
#Takes: a splitline, linenumber
def binarymath(splitline, linenum):		
	cont = 0
	if ((splitline[0] in varnames) and len(splitline) > 4 and splitline[2] != "CALL"): 
		lengthDif = compareLength(splitline[2], splitline[4])
		
		#Get length of longer value
		length = longer(splitline[2], splitline[4])
		
		#Lengths are the same or a val is a literal
		if lengthDif == 0 or lengthDif == None:
			var1 = literal(splitline[2])
			var2 = literal(splitline[4])
			
		#Extends the first or second value as needed		
		#first var is smaller	
		elif lengthDif < 0:
			diff = -lengthDif
			var1 = extend(splitline[2], diff)
			var2 = splitline[4]
			
		#First var is larger	
		elif lengthDif > 0:
			diff = lengthDif
			var1 = splitline[2]
			var2 = extend(splitline[4], diff)

		
		minnib = 1
		suffix = str(length*4)
		
		count = 0
		if splitline[3] == "ADD":
			if length == minnib:
				output.append("ADD " + var1 + " " + var2 + " INTO " + splitline[0])
			else:
				output.append("ADD" + suffix + " " + var1 + " " + var2 + " INTO " + splitline[0])
				
		elif splitline[3] == "SUBTRACT":
			if length == minnib:
				output.append("SUB " + var1 + " " + var2 + " INTO " + splitline[0])
			else:
				output.append("SUB" + suffix + " " + var1 + " " + var2 + " INTO " + splitline[0])
				
		elif splitline[3] == "MULTIPLY":
			#output.append("MULT " + var1 + " " + var2 + " INTO " + splitline[0])
			if length == 16:
				print "Error On line " + str(linenum) + ": Multiplication can not handle larger than 32 bit variables."
			multiply(var1, var2, splitline[0], int(length)*4, linenum)
		elif splitline[3] == "DIVIDE":
			output.append("DIV " + var1 + " " + var2 + " INTO " + splitline[0]) #TODO This doesnt work yet
		elif splitline[3] == "MODULUS":
			output.append("MOD " + var1 + " " + var2 + " INTO " + splitline[0]) #TODO this doesnt work yet
	
		#binary bitwise operators
		elif splitline[3] == "AND":
			if length == minnib:
				output.append("AND " + var1 + " " + var2 + " INTO " + splitline[0])
			else:
				output.append("AND" + suffix + " " + var1 + " " + var2 + " INTO " + splitline[0])
				
		elif splitline[3] == "NAND":
			if length == minnib:
				output.append("NAND " + var1 + " " + var2 + " INTO " + splitline[0])
			else:
				output.append("NAND" + suffix + " " + var1 + " " + var2 + " INTO " + splitline[0])
				
		elif splitline[3] == "OR":
			if length == minnib:
				output.append("OR " + var1 + " " + var2 + " INTO " + splitline[0])
			else:
				output.append("OR" + suffix + " " + var1 + " " + var2 + " INTO " + splitline[0])
				
		elif splitline[3] == "NOR":
			if length == minnib:
				output.append("NOR " + var1 + " " + var2 + " INTO " + splitline[0])
			else:
				output.append("NOR" + suffix + " " + var1 + " " + var2 + " INTO " + splitline[0])
				
		elif splitline[3] == "XOR":
			if length == minnib:
				output.append("XOR " + var1 + " " + var2 + " INTO " + splitline[0])
			else:
				output.append("XOR" + suffix + " " + var1 + " " + var2 + " INTO " + splitline[0])
				
		elif splitline[3] == "XNOR":
			if length == minnib:
				output.append("XNOR " + var1 + " " + var2 + " INTO " + splitline[0])
			else:
				output.append("XNOR" + suffix + " " + var1 + " " + var2 + " INTO " + splitline[0])
			
		#TODO Not sure if this is right, or how to do right shifts/rots at all
		#binary bitshifting
		elif (splitline[3] == "RROTATE"):
			a = ''
			#RROT [label1] into [label2]
		elif (splitline[3] == "LROTATE" ):
			while (count < int(splitline[4])) :
				output.append("LROT" + suffix + " "+ var1 + " INTO " + splitline[0])
				count += 1
			#RROT [label1] into [label2]
		
		elif (splitline[3] == "RSHIFT"):
			a = ''
		elif (splitline[3] == "LSHIFT"):
			while (count < int(splitline[4])) :
				output.append("LSHIFT" + suffix + " "+ var1 + " INTO " + splitline[0])
				count += 1
				
		#binary logical operators
		elif splitline[3] == "ALSO":
			#Not sure if this is correct or not TODO (for both also + either)
			#Check if first val = 0 - if it is jump to fail
			output.append("JMPEQ N_[0] " + var1 + " TO FALSE" + str(linenum))
			#check second val = 0, if it is jump fail
			output.append("JMPEQ N_[0] " + var2 + " TO FALSE" + str(linenum))
			#If made it here both are non0 so true
			output.append("MOV N_[1] INTO " + splitline[0])
			output.append("LOD N_[0]")
			output.append("JMP ENDALSO" + str(linenum))
			#Go here if are false
			output.append("FALSE" + str(linenum) + ":")
			output.append("MOV N_[0] INTO " + splitline[0])
			output.append("ENDALSO" + str(linenum) + ":")
			
		elif splitline[3] == "EITHER":
			#Check if first val is not 0 - if it is jump to true
			output.append("JMPNE N_[0] " + var1 + " TO TRUE" + str(linenum))
			#check second val = 0, if it is jump fail
			output.append("JMPNE N_[0] " + var2 + " TO TRUE" + str(linenum))
			#If made it here both are 0 so false
			output.append("MOV N_[0] INTO " + splitline[0])
			output.append("LOD N_[0]")
			output.append("JMP ENDEITHER" + str(linenum))
			#Go here if either are true
			output.append("TRUE" + str(linenum) + ":")
			output.append("MOV N_[1] INTO " + splitline[0])
			output.append("ENDEITHER" + str(linenum) + ":")
			
		cont = 1
	return cont
	
#Calls the appropriate multiply library call based on the given values - writes the appropriate asm
#Takes- 2 variables, the result label, and the length of the largest variable, and the linenumber
def multiply(var1, var2, result, length, linenum):
	length = str(length)
	op = multinibOp(length, "MOV")
	output.append(op + " " + var1 + " INTO Mult" + length + "_Op1[1]")
	output.append(op + " " + var2 + " INTO Mult" + length + "_Op2[1]")
	output.append("MOVADDR Return" + str(linenum) + " INTO Mult" + length + "_RetAddr[1]")
	output.append("LOD N_[0]")

	#unsgined

	if(var1 not in signed and var2 not in signed):
		
		if int(length) == 4:
			output.append("STR Mult4_Op1[0]")
			output.append("STR Mult4_Op2[0]")
		else:
			output.append("STR Mult" + length + "_Op1Ex")
			output.append("STR Mult" + length + "_Op2Ex")
		output.append("JMP Mult" + length + "_UnsignedEntry")
		
	#signed
	else:
		output.append("JMP Mult" + length + "_SignedEntry")

	output.append("Return" + str(linenum) + ":")
	output.append("NOP 0")
	resLength = varLength(result)
	op = multinibOp(resLength, "MOV")
	output.append(op + " Mult" + length + "_Ans INTO " + result)
		


#Checks if assigning a variable to another variable
#Takes: a splitline
def assignment(splitline, linenum):	
	cont = 0
	if ((splitline[0] in varnames) and ((len(splitline) == 3) or (splitline[2] == "CALL") or splitline[3] == "SIGNED")):
		length = varLength(splitline[0])
		#If assigning a variable to antoehr variable
		if(splitline[2] in varnames):	
			output.append("MOV " + splitline[2] + " INTO " + splitline[0])
		#Function return value
		elif(splitline[2] == "CALL"):
			line = splitline[2:]
			functionCall(line, linenum)
			output.append("MOV " + splitline[3] +  "_RetVal INTO " + splitline[0])
			
		#Literal value assignment
		else: 
			output.append("MOV N_[" + splitline[2] + "] INTO " + splitline[0])	
			
		#Add to signed list	
		if(splitline > 3 and [3] == "SIGNED" and splitline not in signed):
			signed.append(splitline[0])
		cont = 1
	return cont
	
#Checks a line for any conditionals
#Takes: a splitline, linenum
def conditionals(splitline, linenum):
	cont = 0
	if(splitline[0] in ["IF", "ELSEIF", "ELSE", "ENDIF", "LOOPWHILE", "ENDLOOP", "LOOPAGAIN", "EXITLOOP", "EXITIF", "EARLYEND"]):
		label = splitline[0]+str(linenum)+"jump"
		if splitline[0] in ["IF", "ELSEIF", "LOOPWHILE"]:
			staycond = splitline[2]
			if staycond == "EQUALS":
				jumptype = "JMPNE"
			elif staycond == "NOTEQUALS":
				jumptype = "JMPEQ"
			elif staycond == "GREATER":
				jumptype = "JMPLE"
			elif staycond == "GREATEREQUALS":
				jumptype = "JMPL"
			elif staycond == "LESS":
				jumptype = "JMPGE"
			elif staycond == "LESSEQUALS":
				jumptype = "JMPG"
			
			splitline[1] = literal(splitline[1])
			splitline[3] = literal(splitline[3])
				
			if splitline[0] == "IF":
				ifStatementStack.append(label)
				endifStack.append("endif" + str(linenum))
				output.append(jumptype + " " + splitline[1] + " " + splitline[3] + " TO " + label)
				
			elif splitline[0] == "ELSEIF": 
				output.append("JMP "+str(endifStack[-1]))
				output.append(str(ifStatementStack.pop()) + ":")
				ifStatementStack.append(label)
				output.append(jumptype + " " + splitline[1] + " " + splitline[3] + " TO " + label)
				
			elif splitline[0] == "LOOPWHILE":
				output.append("start" + label + ":")
				output.append(jumptype + " " + splitline[1] + " " + splitline[3] + " TO " + label)
				loopStatementStack.append(label)
		
		elif splitline[0] == "ELSE":
			output.append("JMP "+str(endifStack[-1]))
			output.append(str(ifStatementStack.pop()) + ":")
			ifStatementStack.append(label)

		elif splitline[0]== "ENDIF":
			output.append(str(ifStatementStack.pop()) + ":")
			output.append(str(endifStack.pop()) + ":")

		elif splitline[0] == "ENDLOOP":
			label = str(loopStatementStack.pop())
			output.append("JMP start"+label)
			output.append(label + ":")

		#GOTO derivatives
		elif splitline[0] == "LOOPAGAIN":
			output.append("JMP start"+str(loopStatementStack[-1]))
		elif splitline[0] == "EXITLOOP":
			output.append("JMP " + str(loopStatementStack[-1]))
		elif splitline[0] == "EXITIF":
			output.append("JMP "+ str(endifStack[-1]))
	
		#Earlyend
		elif splitline[0] == "EARLYEND":
			output.append("JMP END")	
			
		cont = 1
	return cont
			
#goto and labels
#Takes: splitline
def goto(splitline):
	cont = 0
	cont = 0
	if(splitline[0] in ["GOTO", "LABEL"]):
		if splitline[0] == "LABEL":
			output.append(splitline[1] + ":")
		elif splitline[0] == "GOTO":
			#apparently load 0 before uncoditional jumps
			output.append("LOD N_[0]")
			output.append("JMP " + splitline[1]) 
		cont = 1
	return cont


#Checks if the line contains any function properties
#Takes: splitline
def functionProperties(splitline, linenum):
	cont = 0
	
	global returns
	if splitline[0] == "FUNCTION":
		#Check if function exists:
		if splitline[1] in funcnames:
			print "Error line " + str(linenum) + ": Function " + splitline[1] + " already declared"
		
		#Add to funcnames (plus current funcnames length)
		funcnames.append(splitline[1])
		funcNum = len(funcnames)
		funcvars = ''
		
		#must match declaration sig
		name = splitline[1]
		funcstack.append(name)
		output.append("#" + name + " function begins here")
		#If you ge to here something went wrong so jump to end
		output.append("LOD N_[0]")
		output.append("JMP END")
		
		output.append(name + "Entry:")
		nextparam = 0
		paramnum = 0
		if len(splitline) > 2:
			#just takes
			if splitline[2] == "TAKES":
				nextparam = 2
				# Using 0 as default val for everything
				while len(splitline) > nextparam + 1:
					data.append(name + "_" + splitline[nextparam + 2] +": .data " + splitline[nextparam + 1] + " 0")
					varnames.append(name + "_" + splitline[nextparam + 2])
					varsizes.append(splitline[nextparam + 1])
					funcvars += splitline[nextparam + 2] + " "
					nextparam += 3
					paramnum += 1
					
			elif splitline[2] == "RETURNS":
				#Jsut returns - defaults value to 0 
				data.append(name + "_RetVal: .data " + str(splitline[3]) + " 0")
				if len(splitline) > 4:
					#returns and takes
					nextparam = 4
					while len(splitline) > nextparam + 1:
						data.append(name + "_" + splitline[nextparam + 2] +": .data " + splitline[nextparam + 1] + " 0")
						varnames.append(name + "_" + splitline[nextparam + 2])
						varsizes.append(splitline[nextparam + 1])
						funcvars += splitline[nextparam + 2] + " "
						nextparam += 3
						paramnum += 1
					
			else:
				print "Error  on line " + str(linenum) + ": Not a valid function " +str(splitline[1])
				exit(1)
			
			#Add variable names to funcVars
			funcVars.append(funcvars)
			
		cont = 1
		
	elif splitline[0] == "ENDFUNCTION":
		name = funcstack.pop()
		if returns == 0:
			output.append(name + "_RetAddr:")
			output.append("LOD N_[0]")
			output.append("JMP 0000")
		returns = 0
		cont = 1
		
	elif splitline[0] == "RETURN":
		name = funcstack[-1]
		output.append("MOV " + splitline[1] + " INTO "+ name + "_RetVal")
		output.append("LOD N_[0]")
		output.append(name + "_RetAddr:")
		output.append("JMP 0000")
		returns = 1
		cont = 1
	return cont
	
	

#Checks for and performs function calls
#Takes: splitline, current line number
def functionCall(splitline, linenum): 
	cont = 0
	if splitline[0] == "CALL":
		
		#For this part to work we need to specifiy that functions go at top of program?
		if splitline[1] not in funcnames:
			print "Error on line " + str(linenum) + ": Function " + splitline[1] + " does not exist" 
		
		#Fill the correct var
		funcVarLoc = funcnames.index(splitline[1]) 
		funcvars = funcVars[funcVarLoc].split()
		varcnt = 0
		
		#Has at least one variable
		if len(splitline) >= 3:
			var = literal(splitline[2])
			#output.append("MOV " + var + " INTO " + splitline[1] + "_Param0")
			output.append("MOV " + var + " INTO " + splitline[1] + "_" + funcvars[varcnt])
			varcnt += 1

			#Has 1+ ASWELL in it
			if len(splitline) > 3:
				paramnum = 1
				nextparam = 3
				while (len(splitline) > nextparam + 1):
					var = literal(splitline[nextparam+1])
					#output.append("MOV " + var + " INTO " + splitline[1] + "_Param" + str(paramnum))
					output.append("MOV " + var + " INTO " + splitline[1] + "_" + funcvars[varcnt])
					varcnt += 1
					nextparam += 2
					paramnum += 1
	
		
		output.append("MOVADDR " + splitline[1] + "_Return" + str(linenum) + " INTO " + splitline[1] + "_RetAddr[1]")
		output.append("LOD N_[0]")
		output.append("JMP " + splitline[1] + "Entry")
		output.append(splitline[1] + "_Return" + str(linenum) + ":")
		output.append("NOP 0")
		
		cont = 1
	return cont
	
	
#TODO compelte this
#Checks if a special asm function is being created - creates the required output
#Takes a splitline
def asmFunction(splitline, linenum):
	global asmFunc
	#First call - initialize function params
	if asmFunc == 0:
		#get rid of ASM 
		funcProp = splitline[1:]
		functionProperties(funcProp, linenum)
		asmFunc = 1
	
	#End function
	elif len(splitline) > 2 and splitline[1] == "ENDFUNCTION":
		asmFunc = 0
		funcProp = splitline[1:]
		functionProperties(funcProp, linenum)
	
	#Inside a ASM function
	else:
		temp = ''
		#ASM should fall through and labels should be replaced
		for word in splitline:
			#TODO i think im misinterpreting what Ryan/Naomi want me to do here with the special params?
			if word in varnames:
				temp += "$" + word + " "
			else:
				temp +=  word + " "
		output.append(temp)
			
		

#Checks for included files and does the appropriate stuff for them- can be of type .CB or .s  TODO is it .s?
#Takes a splitline
def includeFile(splitline, linenum):
	cont = 0
	cont = 0
	if len(splitline) == 3 and splitline[0] == "INCLUDE":
		if splitline[1] == "CUTEBASIC":
			files.append(splitline[2])
			
		elif splitline[1] == "ASM":
			asmFile(splitline[2])
			
		else:
			print "Error on line: " + str(linenum) + " Not a valid CB or macro asm file"
			exit(1)
		cont = 1
	return cont

def baseaddr(splitline, linenum):
	if splitline[0] == "BASEADDRESS":
		output.append("INF " + splitline[1])
		baseaddress = int(splitline[1])
		return 1	

#Pretty much the same as the main loop except it uses included files instead, it deletes them from the lsit when they are read in
def inlineFile():
	linenum2 = 1
	inputf2 = open(files[-1], 'r')
	name = files[-1]
	#This loop is the compiler section - converts all lines of CB into lines of Macro ASM
	for line2 in inputf2.readlines():
		#Check for comments
		continueBool = checkComment(line2)
		if continueBool == 1:
			linenum2 += 1
			continue
		
		#Check if line is START or END 
		startEnd(line2)
		
		splitline2 = line2.split()
		
		#Check for empty line 
		if len(splitline2) == 0:
			output.append("") #preserves empty lines, an be changed if unwanted
			linenum2 += 1
			continue
		
		#Check for asm or passthroc, if found then line is passed through unchanged
		continueBool = asm_passthroc(splitline2)
		if continueBool == 1:
			linenum2 += 1
			continue
		
		#Check what the line is	
		variableDeclaration(splitline2, linenum2)
		unarymath(splitline2, linenum2)
		binarymath(splitline2, linenum2)
		assignment(splitline2, linenum2)
		conditionals(splitline2,linenum2)
		goto(splitline2)
		functionProperties(splitline2, linenum2)
		functionCall(splitline2, linenum2)
		#files(splitline,linenum)
		includeFile(splitline2, linenum2)
		linenum2 += 1
	files.remove(name)
	
	
#Takes an ASM file and puts it into our file sepeariting the data and non data sections
#Takes an ASM file 
def asmFile(file):
	#This as been replaced by naomi creating a way to handle this in the macro assembly
	#inputf = open(file, 'r')
	#for line in inputf.readlines():
	#	splitline = line.split()
		#Data type
	#	if(len(splitline) > 1 and splitline[0][-1] == ":"):
	#		data.append(line)
		#Non data
	#	else:
	#output.append(line)
	
	output.append("INCL " + file)


#************************************************************************************ MAIN*********************************************************************************************
def main():
	global output
	global data
	#data.append("########## DATA SECTION BELOW HERE ##########")
	if len(sys.argv) < 2:
		print 'No file specified'
		quit()
	
	
	if len(sys.argv) == 3:
		outputf = open(sys.argv[2], 'w')
	linenum = 1
	
	files.append(sys.argv[1])
	while(files):
		inputf = open(files[0], 'r')

		#This loop is the compiler section - converts all lines of CB into lines of Macro ASM
		for line in inputf.readlines():
			#Check for comments
			continueBool = checkComment(line)
			if continueBool == 1:
				linenum += 1
				continue
			
			#Check if line is START or END 
			continueBool = startEnd(line)
			if continueBool == 1:
				linenum += 1
				continue
			
			
			splitline = line.split()
			#print splitline
			splitline = localVars(splitline)
			#print splitline
			
			#Check for empty line 
			if len(splitline) == 0:
				output.append("") #preserves empty lines, an be changed if unwanted
				linenum += 1
				continue
			
			#Check for asm or passthroc, if found then line is passed through unchanged
			continueBool = asm_passthroc(splitline, linenum)
			if continueBool == 1:
				linenum += 1
				continue
			
			#Check what the line is	
			continueBool = variableDeclaration(splitline, linenum)
			if continueBool == 1:
				linenum += 1
				continue
			
			continueBool = unarymath(splitline, linenum)
			if continueBool == 1:
				linenum += 1
				continue
			
			continueBool = 	binarymath(splitline, linenum)
			if continueBool == 1:
				linenum += 1
				continue
			
			continueBool = assignment(splitline, linenum)
			if continueBool == 1:
				linenum += 1
				continue
			
			continueBool = conditionals(splitline,linenum)
			if continueBool == 1:
				linenum += 1
				continue
			
			continueBool = goto(splitline)
			if continueBool == 1:
				linenum += 1
				continue
			
			continueBool = functionProperties(splitline, linenum)
			if continueBool == 1:
				linenum += 1
				continue
			
			continueBool = functionCall(splitline, linenum)
			if continueBool == 1:
				linenum += 1
				continue
			
			#files(splitline,linenum)
			continueBool = includeFile(splitline, linenum)
			if continueBool == 1:
				linenum += 1
				continue
			
			continueBool = baseaddr(splitline, linenum)
			if continueBool == 1:
				linenum += 1
				continue
	
			#Testing a way to inline include instead of adding it just to end(because then we get issues of stuff being after END)
			while(len(files) > 1):
				inlineFile()
				linenum += 1
				continue
				
			print "Error - Unkown Values in line: " + str(linenum)
			exit(1)
			
			#linenum = linenum + 1
	
	
		inputf.close()
		del files[0]
		
		
	if hasstart == 0:
		print "No START declared!"
		quit(1)
	if hasend == 0:
		print "No END declared!"
		quit(1)
	if hasend == 1 and hasstart == 1:
		if(baseaddress == -1):
			prepend = []
			prepend.append("INF 0x400")
			output = prepend + output  
		output = output + data
		for i in output:
			if(len(sys.argv)) == 3:
				outputf.write(i + "\n")
			#print i
	
	#for i in varsizes:
	#	print i
	#for i in varnames:
	#	print i
	
	quit(0)

# This if only runs if this file is called as a script - if it is included, it doesn't
if __name__ == "__main__":
	main()
