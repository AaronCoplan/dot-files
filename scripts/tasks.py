#!/usr/bin/env python

from sys import argv, exit as sysexit
from subprocess import check_output, CalledProcessError

def main():
    if len(argv) != 2 and len(argv) != 3:
        print('[ERROR] Please provide one argument, the glob path for files to search through.  Optionally provide a second argument for comma separated file types.')
        sysexit(1)

    if not hasGrep():
        print("[ERROR] Missing grep! Please install grep and try again.")
        sysexit(1)

    if len(argv) == 3:
        todos = findTodos(argv[1], argv[2].split(','))
    else:
        todos = findTodos(argv[1])

    printTodos(todos)

def hasGrep():
    try:
        check_output(['grep', '-V'])
        return True
    except CalledProcessError as e:
        return False

def printDashes(length):
    string = ''
    for _ in range(length):
        string += '-'
    print(string)

def printTodos(todos):
    for fileName in todos:
        formattedFileName = '| {} |'.format(fileName)
        length = len(formattedFileName)
        printDashes(length)
        print(formattedFileName)
        printDashes(length)
        for lineNumber,content in todos[fileName]:
            print('{}: {}'.format(lineNumber, content))

def generateGrepCommand(keyword, baseDir, fileTypes=[]):
    fileTypes = [' --include="*.{}"'.format(ft) for ft in fileTypes]
    return 'grep -i -r -n{} {} {}'.format(''.join(fileTypes), keyword, baseDir)

def parseGrepOutput(output):
    parsedLines = [parseGrepLine(line) for line in output.splitlines()]
    fileMap = {}
    for fileName,lineNumber,content in parsedLines:
        if fileName in fileMap:
            fileMap[fileName].append((lineNumber, content))
        else:
            fileMap[fileName] = [(lineNumber, content)]

    return fileMap

def parseGrepLine(line):
    colonIndex = line.find(':')
    fileName = line[:colonIndex]
    line = line[colonIndex+1:]
    colonIndex = line.find(':')
    lineNumber = line[:colonIndex]
    content = line[colonIndex+1:].strip()
    return (fileName, lineNumber, content)


def findTodos(baseDir, fileTypes=[]):
    try:
        command = generateGrepCommand('todo', baseDir, fileTypes)
        grepOutput = check_output(command, shell=True)
        return parseGrepOutput(grepOutput)
    except CalledProcessError as e:
        if e.returncode == 1:
            return []
        print(e.output)
        print(e.returncode)

        print("[ERROR] Failed to look for todos.")
        sysexit(1)

if __name__ == "__main__":
    main()
