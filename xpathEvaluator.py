import re
import requests


import lxml
from lxml import etree, html

tree = etree.HTML(
    """<meta name="msapplication-tap-highlight" content="no" />
				<meta http-equiv="X-UA-Compatible" content="IE=EDGE"/>	
				<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
				<meta name="msapplication-config" content="none"/>
				<meta name="robots" content="noydir" /> 
				<meta name="robots" content="noodp" />""")


forStorage = []

class Lexer():
    chunks = None
    index = 0
    length = 0

    def __init__(self, xpath):
        pattern = re.compile(
            """\$?(?:(?![0-9-])(?:[\w-]+|\*):)?(?![0-9-])(?:[\w-]+|\*)|\(:|:\)|\/\/|\.\.|::|\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|"[^"]*(?:""[^"]*)*"|'[^']*(?:''[^']*)*'|<<|>>|[!<>]=|(?![0-9-])[\w-]+:\*|\s+|.""")
        if(isinstance(xpath, list)):
            self.chunks = xpath
        else:
            self.chunks = re.findall(pattern, xpath)

        self.length = len(self.chunks)
        self.index = 0

    def isEof(self):
        return not(self.index < self.length)

    def now(self, i=0):
        return self.chunks[self.index+i]

    def next(self, i=1):
        self.index += i
        if(self.index < self.length):
            return self.chunks[self.index]
        else:
            return None

    def prev(self, i=1):
        self.index -= i
        if(self.index > -1):
            return self.chunks[self.index]
        else:
            return None

def isForExpr(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'for'):
            forExpr = {"expr":None,"value":[]}
            while(lexer.next()[0]!= '$'):
                pass
            ##print("forExpr",lexer.now())
            forExpr["expr"] = lexer.now()
            
            while(re.match(r"^\s+",lexer.next()) or lexer.now() == 'in'):
                pass
            
            ##print('xpath', lexer.now())
            frm = lexer.index
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == 'for'):
                    i += 1
                elif(lexer.now() == 'return'):
                    i -= 1
                lexer.next()
            lexer.prev()
            to = lexer.index

            ##print("for condition",lexer.chunks[frm:to])

            lx = Lexer(lexer.chunks[frm:to])
            xpath = getChunk(lx)
            txt = tree.xpath(xpath)
            text = getText(txt)
            ##print(text)
            forExpr["value"] = [text]
            
            forStorage.append(forExpr)

            ##print("return", lexer.now())
            lexer.next()

            if(re.match(r"^\s+", lexer.next())):
                lexer.next()
            
            frm = lexer.index
            openBracs = (lexer.now() == '(')
            to = len(lexer.chunks)

            if(re.match(r"^\s+", lexer.chunks[to - 1]) and re.match(r"^\)", lexer.chunks[to - 2])):
                if(openBracs):
                    frm = frm + 1
                    to = to - 2

            elif(re.match(r"^\)", lexer.chunks[to - 1])):
                if(openBracs):
                    frm = frm + 1
                    to = to - 1

            ##print("returnExpr", lexer.chunks[frm:to])
            ##print("forStorage",forStorage)

            for x in lexer.chunks[frm:to]:
                for y in forStorage:
                    ##print(y['expr'],x)
                    if y["expr"] in x:
                        ##print(y['value'])
                        tree.xpath(y['value'])   

            ##print(forExpr)



def isOpenBracs(lexer):
    if(lexer.now() == '('):
        lexer.next()
        ##print("lexer chunks",lexer.chunks)
        frm = lexer.index 
        i = 1
        while(i != 0 and not(lexer.isEof())):
            ##print(lexer.now())
            if(lexer.now() == '('):
                i += 1
            elif(lexer.now() == ')'):
                i -=1 
            lexer.next() 
        lexer.prev()  
        to = lexer.index
        
        ##print("now" , lexer.now())
        ##print("brackets", lexer.chunks[frm:to])

        lx = Lexer(lexer.chunks[frm:to])
        arr = getChunk(lx)
        ##print("arr in brackets", arr)

        txt =  ''.join(lexer.chunks[:frm-1]) + "(" + arr + ''.join(lexer.chunks[to:])

        ##print("brackets Text", txt)
        return txt or ' '

    else:
        return None

def isStartsWith(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'starts-with'):
            while(lexer.next() != '(' and not(lexer.isEof()) ):
                pass
            frm = lexer.index + 1
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            lexer.prev()
            to = lexer.index
            i = 0
            while(i != 1 and not(lexer.isEof())):
                if(lexer.prev() == ','):
                    i += 1

            middle = lexer.index
            ##print("firsrLexer : ", lexer.chunks[frm:middle])
            ##print("secondLexer : ", lexer.chunks[middle + 1:to])
            firstLexer = getChunk(Lexer(lexer.chunks[frm:middle]))
            secondLexer = getChunk(Lexer(lexer.chunks[middle+1 :to]))

            txt = "starts-with(" + firstLexer + ',' + secondLexer +")"

            ###print("replaced Text", txt)
            return txt or ' '

        else:
            return None

def isConcat(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'concat'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass

            frm = lexer.index
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            lexer.prev()
            to = lexer.index

            commaIndex = []
            while(lexer.index > frm and not(lexer.isEof())):
                if(lexer.prev() == ','):
                    commaIndex.append(lexer.index)

            commaIndex.reverse()
            commaIndex.append(to)
            commaIndex = [frm] + commaIndex
            ##print("lexer : ", lexer.chunks, "lexerIndex : ", commaIndex)
            commaLength = len(commaIndex)

            txt = "replace("
            for j in range(commaLength):
                if(j+1 < commaLength):
                    txt += getChunk(
                        Lexer(lexer.chunks[commaIndex[j]+1: commaIndex[j+1]]))
                    if(j != (commaLength - 2)):
                        txt += ','
                  
            txt += ')'

            ##print("replaced Text", txt)
            return txt or ' '

        else:
            return None

def isEndsWith(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'ends-with'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass
            frm = lexer.index + 1
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            lexer.prev()
            to = lexer.index
            i = 0
            while(i != 1 and not(lexer.isEof())):
                if(lexer.prev() == ','):
                    i += 1

            middle = lexer.index
            ##print("firsrLexer : ", lexer.chunks[frm:middle])
            ##print("secondLexer : ", lexer.chunks[middle + 1:to])
            firstLexer = getChunk(Lexer(lexer.chunks[frm:middle]))
            secondLexer = getChunk(Lexer(lexer.chunks[middle+1:to]))

            txt = "ends-with(" + firstLexer + ',' + secondLexer + ")"

            ###print("replaced Text", txt)
            return txt or ' '

        else:
            return None

def isSubstringBefore(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'substring-before'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass
            frm = lexer.index + 1
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            lexer.prev()
            to = lexer.index
            i = 0
            while(i != 1 and not(lexer.isEof())):
                if(lexer.prev() == ','):
                    i += 1

            middle = lexer.index
            ##print("firsrLexer : ", lexer.chunks[frm:middle])
            ##print("secondLexer : ", lexer.chunks[middle + 1:to])
            firstLexer = getChunk(Lexer(lexer.chunks[frm:middle]))
            secondLexer = getChunk(Lexer(lexer.chunks[middle+1:to]))

            txt = "substring-before(" + firstLexer + ',' + secondLexer + ")"

            ###print("replaced Text", txt)
            return txt or ' '

        else:
            return None


def isSubstringAfter(lexer):
    if(lexer.isEof()):
            return
    else:
        if(lexer.now() == 'substring-after'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass
            frm = lexer.index + 1
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            lexer.prev()
            to = lexer.index
            i = 0
            while(i != 1 and not(lexer.isEof())):
                if(lexer.prev() == ','):
                    i += 1

            middle = lexer.index
            ##print("firsrLexer : ", lexer.chunks[frm:middle])
            ##print("secondLexer : ", lexer.chunks[middle + 1:to])
            firstLexer = getChunk(Lexer(lexer.chunks[frm:middle]))
            secondLexer = getChunk(Lexer(lexer.chunks[middle+1:to]))

            txt = "substring-after(" + firstLexer + ',' + secondLexer + ")"

            ###print("replaced Text", txt)
            return txt or ' '

        else:
            return None



def isReplace(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'replace'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass

            frm = lexer.index
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            lexer.prev()
            to = lexer.index

            commaIndex = []
            while(len(commaIndex) != 2 and not(lexer.isEof())):
                if(lexer.prev() == ','):
                    commaIndex.append(lexer.index)
            
            commaIndex.reverse()
            commaIndex.append(to)
            commaIndex = [frm] + commaIndex
            ##print("lexer : ",lexer.chunks,"lexerIndex : ", commaIndex)
            commaLength = len(commaIndex)

            txt = "replace("
            for j in range(commaLength):
                if(j+1 < commaLength):
                    txt += getChunk(Lexer(lexer.chunks[ commaIndex[j]+1 : commaIndex[j+1] ]))
                    ###print(getChunk(Lexer(lexer.chunks[ commaIndex[j]+1 : commaIndex[j+1] ])))
                    if(j != (commaLength - 2)):
                        txt += ','
                    ##print(j," Index : ",''.join(lexer.chunks[ commaIndex[j]+1 : commaIndex[j+1] ]) )
            txt += ')'
           
            ##print("replaced Text", txt)
            return txt or ' '

        else:
            return None


def isTranslate(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'translate'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass

            frm = lexer.index
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            lexer.prev()
            to = lexer.index

            commaIndex = []
            while(len(commaIndex) != 2 and not(lexer.isEof())):
                if(lexer.prev() == ','):
                    commaIndex.append(lexer.index)

            commaIndex.reverse()
            commaIndex.append(to)
            commaIndex = [frm] + commaIndex
            ##print("lexer : ", lexer.chunks, "lexerIndex : ", commaIndex)
            commaLength = len(commaIndex)

            txt = "translate("
            for j in range(commaLength):
                if(j+1 < commaLength):
                    txt += getChunk(
                        Lexer(lexer.chunks[commaIndex[j]+1: commaIndex[j+1]]))
                    if(j != (commaLength - 2)):
                        txt += ','
                  

            txt += ')' 


            ##print("translated Text", txt)
            return txt or ' '

        else:
            return None


def isTokenize(lexer):
    if(lexer.isEof()):
            return
    else:
        if(lexer.now() == 'tokenize'):
            while(lexer.now() != '(' ):
                lexer.next()
            frm = lexer.index + 1
            i = 1
            lexer.next()
            ##print("tokenize start",lexer.now())
            while(i != 0 and not(lexer.isEof())):
                ##print("tokenize now : ", lexer.now(), i)
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            lexer.prev()
            ##print("tokenize To : **** :", lexer.now())
            to = lexer.index
            ##print("tokenize To : **** :", to, lexer.chunks[to] )
            i = 0
            while(i != 1 and not(lexer.isEof())):
                if(lexer.prev() == ','):
                    i += 1

            middle = lexer.index
            ##print("firsrLexer : ", lexer.chunks[frm:middle])
            ##print("secondLexer : ", lexer.chunks[middle + 1:to])
            firstLexer = getChunk(Lexer(lexer.chunks[frm:middle]))
            secondLexer = getChunk(Lexer(lexer.chunks[middle+1:to]))

            txt = "tokenize(" + firstLexer + ',' + secondLexer + ")" + ''.join(lexer.chunks[to+1:])

            ###print("replaced Text", txt)
            return txt or ' '

        else:
            return None


def isStringLength(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'string-length'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass
            lexer.next()
            frm = lexer.index
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            to = lexer.index - 1
            ##print("stringLength-Expr", lexer.chunks[frm:to])
            lx = Lexer(lexer.chunks[frm:to])
            strLenExpr = getChunk(lx)

            ##print("string-Length Xpath", strLenExpr)
            txt = "string-length(" + strLenExpr  + ''.join(lexer.chunks[to:])

            ##print("string length Text", txt)
            return txt or ' '

        else:
            return None


def isDictinctValues(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'distinct-values'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass
            lexer.next()
            frm = lexer.index
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            to = lexer.index - 1

            lx = Lexer(lexer.chunks[frm:to])
            strLenExpr = getChunk(lx)

            txt = "distinct-values(" + strLenExpr + ')'

            return txt or ' '

        else:
            return None


def isUpperCase(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'upper-case'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass
            lexer.next()
            frm = lexer.index
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            to = lexer.index - 1
            
            lx = Lexer(lexer.chunks[frm:to])
            strLenExpr = getChunk(lx)

            
            txt = "upper-case(" + strLenExpr + ')'

            return txt or ' '

        else:
            return None




def isLowerCase(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'lower-case'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass
            lexer.next()
            frm = lexer.index
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            to = lexer.index - 1

            lx = Lexer(lexer.chunks[frm:to])
            strLenExpr = getChunk(lx)

            txt = "lower-case(" + strLenExpr + ')'

            return txt or ' '

        else:
            return None


def ifExpr(lexer):
    if(lexer.isEof()):
        return
    else:
        if(lexer.now() == 'if'):
            while(lexer.next() != '(' and not(lexer.isEof())):
                pass
            lexer.next()
            frm = lexer.index
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == '('):
                    i += 1
                elif(lexer.now() == ')'):
                    i -= 1
                lexer.next()
            to = lexer.index - 1

            # ##print('to', to, lexer.chunks[to:])
            #print("ifExpr", lexer.chunks[frm:to])
            lx = Lexer(lexer.chunks[frm:to])
            ifExpr = getChunk(lx)

            #print("IfExpr Xpath", ifExpr)
            #xpath = tree.xpath(ifExpr)
            #text = getText(xpath)


            try:
                ifExpr = convertAsciitoSymbol(ifExpr)
                #print("Converted",ifExpr)
                xpath = tree.xpath(ifExpr)
                #print(xpath)
                text = getText(xpath)
            except:
                #print('Xpath failed')
                text = None
            
            
            ifExpr = text

            #print('ifExpr Result', ifExpr)

            while(lexer.next() != 'then' and not(lexer.isEof())):
                pass

            if(re.match(r"^\s+", lexer.next())):
                lexer.next()

            frm = lexer.index

            openBracs = (lexer.now() == '(')
            #print(openBracs)
            i = 1
            while(i != 0 and not(lexer.isEof())):
                if(lexer.now() == 'if'):
                    i += 1
                elif(lexer.now() == 'else'):
                    i -= 1
                lexer.next()
            lexer.prev()
            to = lexer.index

            if(re.match(r"^\s+", lexer.now(-1)) and re.match(r"^\)", lexer.now(-2))):
                if(openBracs):
                    frm = frm + 1
                    to = to - 2

            elif(re.match(r"^\)", lexer.now(-1))):
                if(openBracs):
                    frm = frm + 1
                    to = to - 1

            if(ifExpr):
                #print("thenExpr", lexer.chunks[frm:to])
                lx = Lexer(lexer.chunks[frm:to])
                thenExpr = getChunk(lx)
                #print("then_expr result", thenExpr)
                return thenExpr

            if(re.match(r"^\s+", lexer.next())):
                lexer.next()

            frm = lexer.index
            openBracs = (lexer.now() == '(')
            to = len(lexer.chunks)

            if(re.match(r"^\s+", lexer.chunks[to - 1]) and re.match(r"^\)", lexer.chunks[to - 2])):
                if(openBracs):
                    frm = frm + 1
                    to = to - 2

            elif(re.match(r"^\)", lexer.chunks[to - 1])):
                if(openBracs):
                    frm = frm + 1
                    to = to - 1

            #print("elseExpr", lexer.chunks[frm:to])
            lx = Lexer(lexer.chunks[frm:to])
            elseExpr = getChunk(lx)
            #print("else expr result", elseExpr)
            if(elseExpr):
                return elseExpr
            else:
                return '  '


def getChunk(lexer):
    while(not(lexer.isEof())):
        #print(lexer.now())
        
        xpath = isDictinctValues(lexer)
        if(xpath):
            lexer.chunks = xpath
            break

        xpath = isStartsWith(lexer)
        if(xpath):
            lexer.chunks = xpath
            break
        
        xpath = isEndsWith(lexer)
        if(xpath):
            lexer.chunks = xpath
            break

        xpath = isSubstringAfter(lexer)
        if(xpath):
            lexer.chunks = xpath
            break
        
        xpath = isSubstringBefore(lexer)
        if(xpath):
            lexer.chunks = xpath
            break

        xpath = isTokenize(lexer)
        if(xpath):
            lexer.chunks = xpath
            break

        xpath = isOpenBracs(lexer)
        if(xpath):
            lexer.chunks = xpath
            break
        xpath = isReplace(lexer)
        if(xpath):
            lexer.chunks = xpath
            break
        xpath = isStringLength(lexer)
        if(xpath):
            lexer.chunks = xpath
            break
        xpath = isTranslate(lexer)
        if(xpath):
            lexer.chunks = xpath
            break
        xpath = isUpperCase(lexer)
        if(xpath):
            lexer.chunks = xpath
            break
        xpath = isLowerCase(lexer)
        if(xpath):
            lexer.chunks = xpath
            break
        
        xpath = ifExpr(lexer)
        if(xpath):
            return xpath
        

        lexer.next()

    #print("chunks", ''.join(lexer.chunks))

    ''' xpath = tree.xpath(''.join(lexer.chunks))
    #print(xpath)
    text = getText(xpath)
     '''
    return ''.join(lexer.chunks)


def getText(xpath):
    text = None
    #print("xpath Type", type(xpath))

    if(isinstance(xpath, lxml.etree._Element)):
        text = xpath.text

    if(isinstance(xpath, bool)):
        text = xpath

    if(isinstance(xpath, lxml.etree._ElementUnicodeResult)):
        text = str(xpath)

    if(isinstance(xpath, list) and len(xpath) > 0):
        #print("its an list")
        if(isinstance(xpath[0], lxml.etree._Element)):
            text = xpath[0].text

        if(isinstance(xpath[0], lxml.etree._ElementUnicodeResult)):
            text = str(xpath[0])

    #print("From get Xpath", text)
    return text


def getList(xpath):
    text = []
    #print("xpath Type", type(xpath))

    if(isinstance(xpath, lxml.etree._Element)):
        if(xpath.text):
            text = [xpath.text]

    if(isinstance(xpath, lxml.etree._ElementUnicodeResult)):
        if(str(xpath)):
            text = [str(xpath)]

    if(isinstance(xpath, list) and len(xpath) > 0):
        text = []
        for i in xpath:
            #print("its an list",i)
            if(isinstance(i, lxml.etree._Element)):
                if(i.text):
                    text.append(i.text)

            if(isinstance(i, lxml.etree._ElementUnicodeResult)):
                if(str(i)):
                    text.append(str(i))

    #print("From get Xpath", text)
    return text


ns = etree.FunctionNamespace(None)


@ns
def lowercase(context, xpath):
    text = getText(xpath)
    if(text):
        return text.lower()
    else:
        return text


def uppercase(context, xpath):
    text = getText(xpath)
    if(text):
        return text.upper()
    else:
        return text


def replace(context, xpath, text_to_be_replaced, replace_with):
    text = getText(xpath)
    if(text):
        pattern = re.compile(text_to_be_replaced)
        replace_with = replace_with.replace('$','\\')
        #print("replace(",pattern,replace_with,text,")")
        return re.sub(pattern, replace_with, text)
    else:
        return text


def translate(context, xpath, text_to_be_replaced, replace_with):
    text = getText(xpath)
    if(text):
        return text.translate(text_to_be_replaced, replace_with)
    else:
        return text


def startswith(context, xpath, text):
    text_ = getText(xpath)
    if(text_):
        return text_.startswith(text)
    else:
        return text_


def endswith(context, xpath, text):
    text_ = getText(xpath)
    if(text_):
        return text_.endswith(text)
    else:
        return text_

def matches(context, xpath, text):
    text_ = getText(xpath)
    if(text_):
        #print("from Marteches",xpath,text)
        pattern = re.compile(text)
        return bool(re.findall(pattern,xpath[0]))
    else:
        return text_
        
def tokenize(context, xpath, text):
    text_ = getText(xpath)
    if(text_):
        pattern = re.compile(text)
        return re.split(pattern,xpath[0])
    else:
        return text_
    
def distinctValues(context, xpath):
    text_ = getList(xpath)
    #print(text_)
    if(len(text_)):
        uniqueArr = []
        for i in text_:
            if i not in uniqueArr:
                uniqueArr.append(i)
        
        return uniqueArr
        #return '|'.join(uniqueArr)
    else:
        return None





ns['lower-case'] = lowercase
ns['upper-case'] = uppercase
ns['replace'] = replace
ns['translate'] = translate
ns['starts-with'] = startswith
ns['ends-with'] = endswith
ns['matches'] = matches
ns['tokenize'] = tokenize
ns['distinct-values'] = distinctValues


def convertAsciitoSymbol(xpath):
    i = 0
    while(xpath.find('&#', i) > 0):
        start = xpath.find('&#', i)
        end = xpath.find(';', start)+1
        xpath = xpath[:start] + chr(int(xpath[start+2:end-1])) + xpath[end:]
        end = end - (end-start)
        i = end
    return xpath


def evaluateXpath(response, xpath):
    global tree
    dpList = {}
   

    pageFailure = False
    try:
        tree = html.fromstring(response.content)
    except Exception as e:
        pageFailure = str(e)
    
    for i in xpath:
        for key, value in i['dp'].items():
            dp = {"xpath": None, "value": None}
            #print("keys",key)
            dp['xpath'] = value
            if(not(pageFailure)):
                try:
                    lexer = Lexer(value)
                    dpxpath = getChunk(lexer)
                    dpxpath = convertAsciitoSymbol(dpxpath)
                    dp['xpath'] = dpxpath
                    evaluated = tree.xpath(dpxpath)
                    if(evaluated):
                        dp['value'] = getText(evaluated)
                        print(dp['value'])
                        dpList[key] = dp
                        return dpList

                except Exception as e:
                    dp['value'] = str(e)
            else:
                dp['value'] = pageFailure
           
            dpList[key] = dp
            print("key : ",key,"xpath : ",dp['xpath'],"value : ",dp['value'])
    
    return dpList


""" 


    xpathJson = getSanitizedXpath(xpath)

    for key, value in xpathJson:
        #print(key)
        evaluated = tree.xpath(value)
        if(evaluated):
            text = getText(evaluated)
            return {"xpath": i, "value": text}
 """



#print(tree.xpath("//a/text() = 'TEXT'"))

#xpath = """replace(replace("Hello" ,"'"," ") ,"'"," ")"""


xpath = [{'layoutName': 'PRODUCT_DETAIL_PAGE1', 'layoutXpath': "//meta[contains(@sourceurl,'/shop/products/')]", 'scraperBeanName': 'DetailPageItemScrapeConfiguration1', 'dp': {'brand_name': "(if((//div[contains(@class,'breadCrumbs')]//a[@id='lnk']//text())[contains(.,'Software') or contains(.,'Services') or contains(.,'Books')]) then '' else (if (//span[contains(@class,'brand')]) then (//span[contains(@class,'brand')]//text()) else if(//div[contains(@id,'manufacturerLogo')]) then (//div[contains(@id,'manufacturerLogo')]//img/@title|//div[@class='manufacturerLogo']//span//text()) else //div[contains(@id,'innerTSpec')]//td[contains(.,'Brand:')]//following-sibling::td[contains(@class,'data')]//text()[normalize-space()]))[1]"}}, {'layoutName': 'PRODUCT_DETAIL_PAGE2', 'layoutXpath': "//meta[contains(@sourceurl,'/product/')]", 'scraperBeanName': 'DetailPageItemScrapeConfiguration2', 'dp': {'brand_name': "if(//div[contains(@class,'product-breadcrumb')]//ul[contains(@class,'breadcrumbs')]//a[contains(.,'Software') or contains(.,'Books') or contains(.,'Services')]) then '' else(if(string-length(normalize-space(//div[@class='manufacture-logo']/img/@title))>1) then //div[@class='manufacture-logo']/img/@title else //input//@data-manufactureName) "}}]

response = requests.get(
    "https://www.amazon.in/Luzon-Dzire-Inline-Sediment-Quickfit/dp/B01GH71V0C/ref=redir_mobile_desktop?_encoding=UTF8&keywords=ro%20filter%20carbon&pi=AC_SX118_SY170_QL70&qid=1482303103&ref_=mp_s_a_1_30&sr=8-30")

print(response)

print(evaluateXpath(response,xpath ))


