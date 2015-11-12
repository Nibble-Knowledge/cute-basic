#!/usr/bin/python
import sys
import os

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
			
			#output.append("")
			#output.append("")
			#output.append("int main()")
			#output.append("{")
			# Some fun
			#output.append("puts(HEADER);")
			#output.append("puts(\"\");")
			
	elif line.strip() == "END":
		if hasend == 1:
			print "END already declared"
			exit(1)
		else:
			hasend = 1
			#output.append("END:")
			#output.append("return 0;")
			#output.append("}")

		
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
        
        #Check for empty line 
		if len(splitline) == 0:
			output.append("\n") #preserves empty lines, an be changed if unwanted

        #Check for asm or passthroc, if found then line is passed through unchanged
		continueBool = asm_passthroc(splitline)
		if continueBool == 1:
			continue
			
		#Check what the line is	
		#variableDeclaration(splitline)
		#unarymath(splitline, linenum)
		#binarymath(splitline, linenum)
		#assignment(splitline)
		#conditionals(splitline,linenum)
		#goto(splitline)
		#functionProperties(splitline)
		#functionCall(splitline, linenum)
		#files(splitline,linenum)
			
	

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