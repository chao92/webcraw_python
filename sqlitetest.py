import os
import re
import sqlite3
import mechanize
import urllib2
from Bio import Entrez
from bs4 import BeautifulSoup

def initBasicInfo():
    conn = sqlite3.connect('JAMIA.db') #create it if not exists
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS BASICINFO;''')
    c.execute('''CREATE TABLE IF NOT EXISTS BASICINFO
        (PMID TEXT,Title TEXT,DOI TEXT,Authors TEXT,Category TEXT,Citation TEXT,Epub TEXT);''')
    conn.commit()
    c.close()
    conn.close()

def initMesh():
    conn = sqlite3.connect('JAMIA.db') #create it if not exists
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS MESH;''')
    c.execute('''CREATE TABLE IF NOT EXISTS MESH
        (PMID TEXT,Mesh TEXT);''')
    conn.commit()
    c.close()
    conn.close()

def initCitation():
    conn = sqlite3.connect('JAMIA.db') #create it if not exists
    c = conn.cursor()
    # c.execute('''DROP TABLE IF EXISTS CITATION;''')
    c.execute('''CREATE TABLE IF NOT EXISTS CITATION
        (PMID text,Title text,Authors text,Journal text,Date text);''')
    conn.commit()
    c.close()
    conn.close()

def initReference():
    conn = sqlite3.connect('JAMIA.db') #create it if not exists
    c = conn.cursor()
    #c.execute('''DROP TABLE IF EXISTS REFERENCE;''')
    c.execute('''CREATE TABLE IF NOT EXISTS REFERENCE
        (PMID text,Title text,Authors text,Journal text,Date text);''')
    conn.commit()
    c.close()
    conn.close()

def _getPMIDlist(pmidFilePath):
    pmidList=file(pmidFilePath).read().split("\r")#depend on system it could be "\n or \r"
    while pmidList.count('-1') > 0:
        pmidList.remove('-1')
    return pmidList


def _downloadRawData(pmidList):
    medlineFile = os.path.join(baseDir,"medline")#download data from pubmed by pmidList, and save it as medline for retrieve
    
    if not os.path.exists(medlineFile):
        Entrez.email=raw_input("Enter your email address to set the Entrez email parameter.\nPlease see http://biopython.org/DIST/docs/api/Bio.Entrez-module.html for more inofrmation.\nYour email: ")
        handle=Entrez.efetch(db='pubmed',id=pmidList,rettype="medline",retmode="text")
        data=handle.read()
        handle.close()
        outhandle = file(medlineFile,"w") # create if not exists
        outhandle.write(data)
    return medlineFile

def addBasicInfo(pmid,title,DOI,authorList,citation,epub):
    conn = sqlite3.connect('JAMIA.db')
    c = conn.cursor()
    c.execute("INSERT INTO BASICINFO (PMID,Title,DOI,Authors, Citation, Epub) VALUES(?,?,?,?,?,?);",(pmid,title,DOI,','.join(authorList),citation,epub))
    conn.commit()
    c.close()
    conn.close()

def addMeSH(meshList,pmid):
    conn = sqlite3.connect('JAMIA.db')
    c = conn.cursor()
    for item in meshList:
        c.execute("INSERT INTO MESH (PMID,Mesh) VALUES (?,?);",(pmid,item))
        conn.commit()
    c.close()
    conn.close()

def _MEDLINEparser(text):
    """parse medline plain text for BASICINFO table"""
    recs = text.split("\n")
    firstLine = True
    meshList = []
    pmid_mesh_dict = {}
    authorList = []
    title = ""
    secondTitle = False
    thirdTitle = False
    DOI = ""
    secondSo = False
    for line in recs:
        
        if line.startswith("PMID-"):
            pmid = line.split("- ")[1].strip("\n") #\n\r if ubuntu
            firstLine = False
        
        elif line.startswith("TI  - "):
            title = line.split("- ")[1].strip("\n") #\n\r if ubuntu
            firstLine = False
            secondTitle= True
        
        elif line.startswith("PG  - "):
            secondTitle = False
            thirdTitle = False
        elif line.startswith("LID - "):
            secondTitle = False
            thirdTitle = False
        
        elif secondTitle and line.startswith("      "):
            title = title + " " + line.strip()#\n\r if ubuntu
            secondTitle = False
            thirdTitle = True
        
        elif thirdTitle and line.startswith("      "):
            title = title + " " + line.strip()#\n\r if ubuntu
            thirdTitle = False
        
        elif line.startswith("AU  - "):
            author = line.split("- ")[1].strip("\n") #\n\r if ubuntu
            authorList.append(author)
            firstLine = False
        
        elif line.startswith("MH  - "):
            meshRaw = line.split("MH  - ")[1].strip("\n") # \n\r if ubuntu
            #  mesh = meshRaw.split("/")[0].strip("*")
            meshList.append(meshRaw)
            firstLine = False
        
        elif line.startswith("AID - "):
            doi = line.split("- ")[1].strip("\n") #\n\r if ubuntu
            match = re.search(r'[\d.]+/[\w/.-]+', doi)
            if match is not None:
                DOI = match.group()
                firstLine = False
    
        elif line.startswith("SO  - "):
            so = line.split("- ")[1].strip("\n") #\n\r if ubuntu
            firstLine = False
            secondSo= True

        elif secondSo and line.startswith("      "):
            so = so + " " + line.strip()#\n\r if ubuntu
            firstLine = False
            secondSo = False
    
        elif (not firstLine) and line=="":
            pmid_mesh_dict[pmid]=meshList
            match1 = re.search(r'[\w\s]+.[\s\w-]+[;]*[\w]+[\(]*[\w]*[\)]*[:]*[\w]*[-]*[\w]*', so)
            match2 = re.search(r'Epub[\w\s]+', so)
            replace = ""
            address = ""
            if match1 is not None:
                address = match1.group()
            #print type(address)
            if match2 is not None:
                Epub = match2.group()
                replace = Epub.replace(Epub[:4], '').strip()
            # print pmid,title,DOI,authorList,address,replace
            addBasicInfo(pmid,title,DOI,authorList,address,replace)
            addMeSH(meshList,pmid)
            meshList=[]
            authorList=[]

def _retMEDLINE(medline):
    fin=file(medline).read()[:-1] # remove the last empty row to standardize the format
    citationList = fin.split("\n\n") # split the file by citation
    for citation in citationList:
        citation+="\n" # reformat every citation
        _MEDLINEparser(citation)

def createTableBasicInfo(pmidFilePath):
    initBasicInfo()
    initMesh()
    pmidList = _getPMIDlist(pmidFilePath)
    medline = _downloadRawData(pmidList)
    _retMEDLINE(medline)

def _getResultURL(mode,text):
    #the search page of web of science
    searchURL = "http://apps.webofknowledge.com/UA_GeneralSearch_input.do?product=UA&search_mode=GeneralSearch&SID=2AkR6Gt4nU7x1c8tniD&preferencesSaved="
    br = mechanize.Browser()
    br.open(searchURL)
    br.select_form(name="UA_GeneralSearch_input_form")
    br.form["value(input1)"]=text
    controlItem = br.form.find_control("value(select1)",type="select")
    if mode == 1:
        controlItem.value = ['DO']
    elif mode == 2:
        print "using title to search"
        controlItem.value = ['TI']
    request = br.form.click()
    response = mechanize.urlopen(request)
    return response.geturl()

def nextPageExist(soup):
    lists = soup.find("a",attrs={"class": "paginationNext"})
    if lists['href'] == "javascript: void(0)":
        return None
    else:
        return lists['href']

def _addCitaLists(pmid,url):
    conn = sqlite3.connect('JAMIA.db') #create it if not exists
    c = conn.cursor()
    soup = BeautifulSoup(urllib2.urlopen(url).read())
    firsttime = True
    nexturl = nextPageExist(soup)
    while firsttime or nexturl is not None:
        lists = soup.find_all("div", class_="search-results-content")
        for tag in lists:
            title = tag.find("value",attrs={"lang_id": ""}).get_text().strip()
            authorss = tag.find("span",text=re.compile("By: "))
            if authorss is not None:
                authors = authorss.parent.get_text().strip()[4:]
            else:
                authors = ""
            journal = tag.find("source_title_txt_label").get_text().strip()
            date = tag.find(text=re.compile("Published: ")).next_element.get_text()
            # print pmid,title,authors,journal,date
            c.execute("insert into CITATION (PMID,Title,Authors,Journal,Date) values (?,?,?,?,?)",(pmid,title,authors,journal,date))
            conn.commit()
        if firsttime and nexturl is not None:
            soup = BeautifulSoup(urllib2.urlopen(nexturl).read())
            firsttime = False
        elif firsttime and nexturl is None:
            break
        else:
            nexturl = nextPageExist(soup)
            if nexturl is not None:
                soup = BeautifulSoup(urllib2.urlopen(nexturl).read())
                firsttime = False
    c.close()
    conn.close()

def _addRefeLists(pmid,url):
    conn = sqlite3.connect('JAMIA.db') #create it if not exists
    c = conn.cursor()
    soup = BeautifulSoup(urllib2.urlopen(url).read())
    firsttime = True
    nexturl = nextPageExist(soup)
    while firsttime or nexturl is not None:
        lists = soup.find_all("div", class_="search-results-item")
        for tag in lists:
            #titles
            titles =tag.find("value",attrs={"lang_id": ""})
            if titles is not None:
                title = titles.get_text().strip()
            else: title = ""
            #authors
            authorss = tag.find("span",text=re.compile("By: "))
            editorss = tag.find("span",text=re.compile("Edited by: "))
            if authorss is not None:
                authors = authorss.parent.get_text().strip()[4:]
            elif editorss is not None:
                authors = editorss.parent.get_text().strip()[11:]
            else:
                authors = ""
            #journal
            conference = tag.find("span",text=re.compile("Conference:"))
            if conference is not None:
                journals=conference.parent.get_text().strip().split(':')
                journal = ' '.join(journals[1].split()[:-1])
            elif authorss is not None:
                infor = authorss.parent.findNext('div')
                inforlists = infor.get_text().strip().split(':')
                journal = ' '.join(inforlists[0].split()[:-1])
            elif editorss is not None:
                infor = editorss.parent.findNext('div')
                inforlists = infor.get_text().strip().split(':')
                journal = ' '.join(inforlists[0].split()[:-1])
            else:
                journal = ""
            #specialcase publisher
            publisher = tag.find("span",text=re.compile("Publisher: "))
            if publisher is not None:
                title = journal
                journal = publisher.parent.get_text().split(':')[1].strip()
            #date
            dates = tag.find(text=re.compile("Published:"))
            if dates is not None:
                date = dates.next_element.get_text().strip()
            else:
                date = ""
            c.execute("insert into REFERENCE (PMID,Title,Authors,Journal,Date) values (?,?,?,?,?)",(pmid,title,authors,journal,date))
            conn.commit()
        if firsttime and nexturl is not None:
            soup = BeautifulSoup(urllib2.urlopen(nexturl).read())
            firsttime = False
        elif firsttime and nexturl is None:
            break
        else:
            nexturl = nextPageExist(soup)
            if nexturl is not None:
                soup = BeautifulSoup(urllib2.urlopen(nexturl).read())
                firsttime = False
    c.close()
    conn.close()

def _parseURL(pmid,reURL):
    #  print pmid,reURL
    contents = urllib2.urlopen(reURL).read()
    soup = BeautifulSoup(contents)
    #entering to the page from the result page
    URL = soup.find("a",attrs={"class": "smallV110"})#only one result normally
    if URL is not None:
        url = "http://apps.webofknowledge.com"+URL['href']
        contents2 = urllib2.urlopen(url).read()
        soup2 = BeautifulSoup(contents2)
        #find the cited and reference lists of above paper
        citedlists2 = soup2.find("a",attrs={"title": "View all of the articles that cite this one"})
        referlists2 = soup2.find("a",attrs={"title": "View this record\'s bibliography"})
        #print referlists2
        if citedlists2 is not None:
            ciurl2 = "http://apps.webofknowledge.com" + citedlists2['href']
            _addCitaLists(pmid,ciurl2)
        if referlists2 is not None:
            reurl2 = "http://apps.webofknowledge.com" + referlists2['href']
            _addRefeLists(pmid,reurl2)
    else:
        print "Cannot find the data of PMID =",pmid


def citationNetwork():
    initCitation()
    initReference()
    conn = sqlite3.connect('JAMIA.db')
    cursor = conn.execute("SELECT PMID,Title,DOI FROM BASICINFO")
    pmidList = []
    titleList = []
    doiList = []
    for row in cursor:
        pmidList.append(row[0])
        titleList.append(row[1])
        doiList.append(row[2])
    conn.close()

    for i in range(178,len(pmidList)):
        print i
        print "\n"
        pmid = pmidList[i]
        title = titleList[i]
        doi = doiList[i]
        if doi:
            print "doi searching+++++++"
            reURL = _getResultURL(1,doi)
            print pmid,reURL
            if reURL is not None:
                _parseURL(pmid,reURL)
        elif title:
            print "title searching"
            reURL = _getResultURL(2,title)
            print pmid,reURL
            if reURL is not None:
                _parseURL(pmid,reURL)
        else:
            print "Cannot find the data of PMID =",pmid


if __name__ == '__main__':
    baseDir = os.getcwd()
    pmidFilePath = os.path.join(baseDir,"pmidList.txt")
    if not os.path.exists(pmidFilePath):
        print "Please provide a file of PMID. One PMID per line. Name this file with 'pmidList.txt' and leave it in the current working directory."
    else:
        #create two tables:
        #BASICINFO(PMID,Title,DOI,Authors,Category,Citation,Epub)
        #MESH(PMID,Mesh)
        #createTableBasicInfo(pmidFilePath)
        
        citationNetwork()

