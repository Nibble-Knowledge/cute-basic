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
vartypes = ["BINARY", "HEX", "CHAR"] #TODO add this stuff in (update langspec too)
varsizes = []
varvals = []
varstofree = []

funcnames = []
funcstack = []
returns = 0

signed = []

#flags
hasstart = 0
hasend = 0
multicomment = 0



#Checks the nibble length of the variable
#Takes name of variable
#Returns length of variable 
def varLength(varname):
	if varname in varnames:
		index = varnames.index(varname)
		length = varsizes[index]
		return int(length)
	

#Check the length of two lines and return the difference between them (-# means var 1 is smaller by # nibs, 0 means even, +# means var 1 is bigger by # nibs)	
#Takes 2 variables
#Returns an integer (differnece in size)
def compareLength(varname1, varname2):
	if(varname1 in varnames and varname2 in varnames):
		length1 = varLength(varname1)
		length2 = varLength(varname2)
		return length1 - length2
		
#Checks if a value is a variable or literal, and adds the N_[] if its a literal
#Takes a potential variable
#Returns the same var, or an encased literal
def literal(var):
	if var not in varnames:
		var = "N_[" + var + "]"
	return var

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
			exit(1)
		else:
			hasstart = 1
			output.append("START:")
			
	elif line.strip() == "END":
		if hasend == 1:
			print "END already declared"
			exit(1)
		else:
			hasend = 1
			output.append("END:")

		
#Checks if a line is asm or passthroc, if it is put it directly into output as is
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


#Checks if variable declaration is being performed
#Takes: a splitline
def variableDeclaration(splitline, linenum):
	if splitline[0] == "LET":
		#LET VAR - this should default a size and value
		#LET VAR AS SIZE- this should default a value
		#LET VAR BE VAL (SIGNED)- this should default a size, and if no signed default unsigned
		#LET VAR AS SIZE BE VAL (SIGNED) - if no signed, default unsigned
		
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
		
		
		
		#Check if a local variable
		if len(funcstack) > 0:
			temp +=  funcstack[-1] + "_"
			varnames.append(funcstack[-1] + "_" + splitline[1])
		
		temp += splitline[1]
		
		defaultSize = 4
		defaultVal = 0
		
		#LET VAR
		if len(splitline) == 2:
			temp +=": .data " + str(defaultSize) + " " + str(defaultVal)
			varsizes.append(defaultSize)

		#LET VAR AS or LET VAR AS BE
		elif splitline[2] == "AS":
			#LET VAR AS
			if len(splitline) == 4:
				temp += ": .data " + splitline[3] + " " + str(defaultVal)
				varsizes.append(splitline[3])

			#LET VAR AS BE	
			else:
				if(splitline[5][0] == "\""):
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
			print "Invalid line " + str(linenum) + ": " + str(splitline)
			exit(1)
		#If last input is signed	#TODO figure out what this should do
		if splitline[-1] == "SIGNED":
			signed.append(splitline[1])
			
			
		data.append(temp)
		

#Checks if unary math operations are being performed with assignments as the first thing on the line
#Takes: a splitline
def unarymath(splitline, linenum):	
	if (len(splitline) > 3 and (splitline[0] in varnames) and (splitline[2] in ["COMPLEMENT", "NEGATE", "INCREMENT", "DECREMENT", "NOT", "ADDRESSOF", "CONTENTOF"])): 
		#unary math/bit/logic operators
		if splitline[2] == "COMPLEMENT":
			output.append("NOT " + splitline[3] + " INTO " + splitline[0])
		elif splitline[2] == "NEGATE":
			output.append("NEG " + splitline[3] + " INTO " + splitline[0])
		elif splitline[2] == "INCREMENT":
			output.append("INC " + splitline[3] + " INTO " + splitline[0])
		elif splitline[2] == "DECREMENT":
			#output.append("LOD N_[1]")
			output.append("SUB " + splitline[2] + " N_[1] INTO " + splitline[0]) #TODO double check this
		elif splitline[2] == "NOT":
			output.append("LOGNOT ACC")
			#TODO Dont think this is right but have to double check - only accumualtor lognot?
		elif splitline[2] == "ADDRESSOF":
			a = '' 
			#TODO no idea yet
		elif splitline[2] == "CONTENTOF":
			a = ''
			#TODO no idea yet
	
#Checks if binary math operations are being performed with assignments as the first thing on the line
#Takes: a splitline, linenumber
def binarymath(splitline, linenum):					
	if ((splitline[0] in varnames) and len(splitline) > 4): 
		lengthDif = compareLength(splitline[2], splitline[4])
		
		#Lengths are the same or a val is a literal
		if lengthDif == 0 or lengthDif == None:
			if(splitline[2] not in varnames):
				var1 = "N_[" + splitline[2] + "]"
			else:
				var1 = splitline[2]
				
			if splitline[4] not in varnames:
				var2 = "N_[" + splitline[4] + "]"
			else:
				var2 = splitline[4]
				
		#first var is smaller	#TODO do these elifs
		elif lengthDif < 0:
			diff = -lengthDif
			
			var1 = splitline[2]
			var2 = splitline[4]
		#First var is larger	
		elif lengthDif > 0:
			var1 = splitline[2]
			var2 = splitline[4]

		
		count = 0
		if splitline[3] == "ADD":
			output.append("ADD " + var1 + " " + var2 + " INTO " + splitline[0])
		elif splitline[3] == "SUBTRACT":
			output.append("SUB " + var1 + " " + var2 + " INTO " + splitline[0])
		elif splitline[3] == "MULTIPLY":
			output.append("MULT " + var1 + " " + var2 + " INTO " + splitline[0])
		elif splitline[3] == "DIVIDE":
			output.append("DIV " + var1 + " " + var2 + " INTO " + splitline[0]) #TODO This doesnt work yet
		elif splitline[3] == "MODULUS":
			output.append("MOD " + var1 + " " + var2 + " INTO " + splitline[0]) #TODO this doesnt work yet
	
		#binary bitwise operators
		elif splitline[3] == "AND":
			output.append("AND " + var1 + " " + var2 + " INTO " + splitline[0])
		elif splitline[3] == "NAND":
			output.append("NAND " + var1 + " " + var2 + " INTO " + splitline[0])
		elif splitline[3] == "OR":
			output.append("OR " + var1 + " " + var2 + " INTO " + splitline[0])
		elif splitline[3] == "NOR":
			output.append("NOR " + var1 + " " + var2 + " INTO " + splitline[0])
		elif splitline[3] == "XOR":
			output.append("XOR " + var1 + " " + var2 + " INTO " + splitline[0])
		elif splitline[3] == "XNOR":
			output.append("XNOR " + var1 + " " + var2 + " INTO " + splitline[0])
			
		#TODO Not sure if this is right, or how to do right shifts/rots at all
		#binary bitshifting
		elif (splitline[3] == "RROTATE"):
			a = ''
			#RROT [label1] into [label2]
		elif (splitline[3] == "LROTATE" ):
			while (count < int(splitline[4])) :
				output.append("LROT " + var1 + " INTO " + splitline[0])
				count += 1
			#RROT [label1] into [label2]
		
		elif (splitline[3] == "RSHIFT"):
			a = ''
		elif (splitline[3] == "LSHIFT"):
			while (count < int(splitline[4])) :
				output.append("LSHIFT " + var1 + " INTO " + splitline[0])
				count += 1
				
		#TODO Ask naomi about this too
		#binary logical operators
		elif splitline[3] == "ALSO":
			a = ''
		elif splitline[3] == "EITHER":
			a = ''
	

#Checks if assigning a variable to another variable
#Takes: a splitline
def assignment(splitline, linenum):					
	if ((splitline[0] in varnames) and ((len(splitline) == 3) or (splitline[2] == "CALL"))):
		length = varLength(splitline[0])
		#If assigning a variable to antoehr variable
		if(splitline[2] in varnames):	
			output.append("MOV " + splitline[2] + " INTO " + splitline[0])
		#Function return value
		elif(splitline[2] == "CALL"):
			line = splitline[2:]
			print splitline
			print line
			functionCall(line, linenum)
			output.append("MOV " + splitline[3] +  "_RetVal INTO " + splitline[0])
			
		#Literal value assignment
		else: 
			output.append("MOV N_[" + splitline[2] + "] INTO " + splitline[0])		
		
#Checks a line for any conditionals
#Takes: a splitline, linenum
def conditionals(splitline, linenum):
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
				
			if splitline[0] == "IF":
				ifStatementStack.append(label)
				endifStack.append("endif" + str(linenum))
				output.append(jumptype + " " + splitline[1] + " " + splitline[3] + " TO " + label)
				
			elif splitline[0] == "ELSEIF": 
				output.append("jmp "+str(endifStack[-1]))
				output.append(str(ifStatementStack.pop()) + ":")
				ifStatementStack.append(label)
				output.append(jumptype + " " + splitline[1] + " " + splitline[3] + " TO " + label)
				
			elif splitline[0] == "LOOPWHILE":
				output.append("start" + label + ":")
				output.append(jumptype + " " + splitline[1] + " " + splitline[3] + " TO " + label)
				loopStatementStack.append(label)
		
		elif splitline[0] == "ELSE":
			output.append("jmp "+str(endifStack[-1]))
			output.append(str(ifStatementStack.pop()) + ":")

		elif splitline[0]== "ENDIF":
			output.append(str(endifStack.pop()) + ":")

		elif splitline[0] == "ENDLOOP":
			label = str(loopStatementStack.pop())
			output.append("jmp start"+label)
			output.append(label + ":")

		#GOTO derivatives
		elif splitline[0] == "LOOPAGAIN":
			output.append("jmp start"+str(loopStatementStack[-1]))
		elif splitline[0] == "EXITLOOP":
			output.append("jmp " + str(loopStatementStack[-1]))
		elif splitline[0] == "EXITIF":
			output.append("jmp "+ str(ifStatementStack[-1]))
	
		#Earlyend
		elif splitline[0] == "EARLYEND":
			output.append("jmp END")	
			
#goto and labels
#Takes: splitline
def goto(splitline):
	if(splitline[0] in ["GOTO", "LABEL"]):
		if splitline[0] == "LABEL":
			output.append(splitline[1] + ":")
		elif splitline[0] == "GOTO":
			#apparently load 0 before uncoditional jumps
			output.append("LOD N_[0]")
			output.append("JMP " + splitline[1]) 
		


#Checks if the line contains any function properties
#Takes: splitline
def functionProperties(splitline):
	global returns
	if splitline[0] == "FUNCTION":
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
				#todo should i use names? they complicate things, also using 0 as default val for everything
				while len(splitline) > nextparam + 1:
					data.append(name + "_Param" + str(paramnum) +": .data " + splitline[nextparam + 1] + " 0")
					nextparam += 3
					paramnum += 1
					
			elif splitline[2] == "RETURNS":
				#Jsut returns - defaults value to 0 
				data.append(name + "_RetVal: .data " + str(splitline[3]) + " 0")
				if len(splitline) > 4:
					#returns and takes
					nextparam = 4
					while len(splitline) > nextparam + 1:
						data.append(name + "_Param" + str(paramnum) +": .data " + splitline[nextparam + 1] + " 0")
						nextparam += 3
						paramnum += 1
					
			else:
				print "Not a valid function " +str(splitline[1]) + " on line " + str(linenum)
				exit(1)
		
		
	elif splitline[0] == "ENDFUNCTION":
		name = funcstack.pop()
		if returns == 0:
			output.append(name + "_RetAddr:")
			output.append("LOD N_[0]")
			output.append("JMP 0000")
		returns = 0
		
	elif splitline[0] == "RETURN":
		name = funcstack[-1]
		output.append("MOV " + splitline[1] + " INTO "+ name + "_RetVal")
		output.append("LOD N_[0]")
		output.append(name + "_RetAddr:")
		output.append("JMP 0000")
		returns = 1

#Checks for and performs function calls
#Takes: splitline, current line number
def functionCall(splitline, linenum): 
	if splitline[0] == "CALL":
		
		#Has at least one variable
		if len(splitline) >= 3:
			var = literal(splitline[2])
			output.append("MOV " + var + " INTO " + splitline[1] + "_Param0")
			
			#Has 1+ ASWELL in it
			if len(splitline) > 3:
				paramnum = 1
				nextparam = 3
				while (len(splitline) > nextparam + 1):
					var = literal(splitline[nextparam+1])
					output.append("MOV " + var + " INTO " + splitline[1] + "_Param" + str(paramnum))
					nextparam += 2
					paramnum += 1
	
		
		output.append("MOVADDR " + splitline[1] + "_Return" + str(linenum) + " INTO " + splitline[1] + "_RetAddr[1]")
		output.append("LOD N_[0]")
		output.append("JMP " + splitline[1] + "Entry")
		output.append(splitline[1] + "_Return" + str(linenum) + ":")
		output.append("NOP 0")
		


#************************************************************************************ MAIN*********************************************************************************************
def main():
	global output
	global data
	#data.append("########## DATA SECTION BELOW HERE ##########")
	if len(sys.argv) < 2:
		print 'No file specified'
		quit()
	inputf = open(sys.argv[1], 'r')
	
	if len(sys.argv) == 3:
		outputf = open(sys.argv[2], 'w')
	linenum = 1
	
	
	#This loop is the compiler section - converts all lines of CB into lines of Macro ASM
	for line in inputf.readlines():
		#Check for comments
		continueBool = checkComment(line)
		if continueBool == 1:
			linenum += 1
			continue
		
		#Check if line is START or END 
		startEnd(line)
		
		splitline = line.split()
		
		#Check for empty line 
		if len(splitline) == 0:
			output.append("") #preserves empty lines, an be changed if unwanted
			linenum += 1
			continue
		
		#Check for asm or passthroc, if found then line is passed through unchanged
		continueBool = asm_passthroc(splitline)
		if continueBool == 1:
			linenum += 1
			continue
		
		#Check what the line is	
		variableDeclaration(splitline, linenum)
		unarymath(splitline, linenum)
		binarymath(splitline, linenum)
		assignment(splitline, linenum)
		conditionals(splitline,linenum)
		goto(splitline)
		functionProperties(splitline)
		functionCall(splitline, linenum)
		#files(splitline,linenum)
		
		linenum = linenum + 1
	
	inputf.close()
	if hasstart == 0:
		print "No START declared!"
		quit(1)
	if hasend == 0:
		print "No END declared!"
		quit(1)
	if hasend == 1 and hasstart == 1:
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