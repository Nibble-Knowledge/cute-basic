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

	

#Checks if unary math operations are being performed with assignments as the first thing on the line
#Takes: a splitline
def unarymath(splitline, linenum):	
	if ((splitline[0] in varnames) and (splitline[2] in ["COMPLEMENT", "NEGATE", "INCREMENT", "DECREMENT", "NOT", "ADDRESSOF", "CONTENTOF"])): 
		#unary math/bit/logic operators
		if splitline[2] == "COMPLEMENT":
			output.append("NOT " + splitline[3] + " INTO " + splitline[0])
		elif splitline[2] == "NEGATE":
			output.append("NEG " + splitline[3] + " INTO " + splitline[0])
		elif splitline[2] == "INCREMENT":
			output.append("INC " + splitline[3] + " INTO " + splitline[0])
		elif splitline[2] == "DECREMENT":
			output.append("DEC " + splitline[3] + " INTO " + splitline[0]) #TODO cant tell if implemetned yet outside of accumulator
		elif splitline[2] == "NOT":
			output.append("LOGNOT ACC")
			#TODO Dont think this is right but have to double check
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
	
		if splitline[3] == "ADD":
			output.append("ADD " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0])
		elif splitline[3] == "SUBTRACT":
			output.append("SUB " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0])
		elif splitline[3] == "MULTIPLY":
			output.append("MULT " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0])
		elif splitline[3] == "DIVIDE":
			output.append("DIV " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0]) #TODO This doesnt work yet
		elif splitline[3] == "MODULUS":
			output.append("MOD " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0]) #TODO this doesnt work yet
	
		#binary bitwise operators
		elif splitline[3] == "AND":
			output.append("AND " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0])
		elif splitline[3] == "NAND":
			output.append("NAND " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0])
		elif splitline[3] == "OR":
			output.append("OR " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0])
		elif splitline[3] == "NOR":
			output.append("NOR " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0])
		elif splitline[3] == "XOR":
			output.append("XOR " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0])
		elif splitline[3] == "XNOR":
			output.append("XNOR " + splitline[2] + " " + splitline[4] + " INTO " + splitline[0])
			
		#TODO Ask naomi about shifting and rotating in her code
		#binary bitshifting
		elif (splitline[3] == "RROTATE" or splitline[3] == "RSHIFT"):
			a = ''
			#RROT [label1] into [label2]
		elif (splitline[3] == "LROTATE" or splitline[3] == "LSHIFT"):
			a = ''
			#RROT [label1] into [label2]
		
		#TODO Ask naomi about this too
		#binary logical operators
		elif splitline[3] == "ALSO":
			a = ''
		elif splitline[3] == "EITHER":
			a = ''
		
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
				output.append(jumptype + " " + splitline[1] + " " + splitline[3] + " TO " + label)#TODO what is this label if there is no elseif/else?
				
			elif splitline[0] == "ELSEIF": #TODO figure out elseif and else
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
			output.append("JMP " + splitline[1]) #TODO check if straight jump works in macro otherwise will need to change this
		

#************************************************************************************ MAIN*********************************************************************************************
def main():

	if len(sys.argv) < 2:
		print 'No file specified'
		quit()
	inputf = open(sys.argv[1])
	linenum = 1
	
	
	#This loop is the compiler section - converts all lines of CB into lines of Macro ASM
	for line in inputf.readlines():
		#Check for comments
		continueBool = checkComment(line)
		if continueBool == 1:
			continue
		
		#Check if line is START or END TODO determine what needs to be passed to asm for this part
		startEnd(line)
		
		splitline = line.split()
		
		#Check for empty line 
		if len(splitline) == 0:
			output.append("") #preserves empty lines, an be changed if unwanted
			continue
		
		#Check for asm or passthroc, if found then line is passed through unchanged
		continueBool = asm_passthroc(splitline)
		if continueBool == 1:
			continue
		
		#Check what the line is	
		#variableDeclaration(splitline)
		unarymath(splitline, linenum)
		binarymath(splitline, linenum)
		#assignment(splitline)
		conditionals(splitline,linenum)
		goto(splitline)
		#functionProperties(splitline)
		#functionCall(splitline, linenum)
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
		for i in output:
			print i
	quit(0)

# This if only runs if this file is called as a script - if it is included, it doesn't
if __name__ == "__main__":
	main()