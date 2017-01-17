import os
import re
import sqlite3
import mechanize
import urllib2
import sys
#from Bio import Entrez
from bs4 import BeautifulSoup
from selenium import webdriver
from random import randint
from time import sleep


chrome_browser = webdriver.Chrome()

def BibTeXfromURL(URL):
    chrome_browser.get(URL)
    # get BibTex
    # get drop menu first
    download_menu = chrome_browser.find_element_by_id("gsc_btn_exp-bd")
    download_menu.click()
    # select export as BibTex
    bibitem = download_menu.find_element_by_xpath("//div[@class='gs_md_se gs_vis']")
    item = bibitem.find_element_by_xpath("//li[contains(text(), 'BibTeX')]")
    item.click()

    # save the BibTeX to file

    prune = BeautifulSoup(chrome_browser.page_source)
    with open("BibTeX.bib","a") as myfile:
        myfile.write(prune.find('pre').text.encode('utf-8'))

    # chrome_browser.close()
    # sleep(randint(10,20))

if __name__ == '__main__':
    scholar_Link = sys.argv[1]
    paper_begin = sys.argv[2]
    paper_end = sys.argv[3]
#     xiaoqian_scholar = "https://scholar.google.com/citations?user=DSmxHuMAAAAJ&hl=en"
    # page = urllib2.urlopen(xiaoqian_scholar);
    # soup = BeautifulSoup(page)
    
    chrome_browser.get(scholar_Link)
    showmore_button = chrome_browser.find_element_by_id("gsc_bpf_more")
    while showmore_button.is_enabled():
        showmore_button.click()
        sleep(3)
    # after click

    # print type(chrome_browser.page_source)
    # scholarPage = BeautifulSoup(chrome_browser.page_source, "html5lib")
    wholeTable = chrome_browser.find_element_by_id("gsc_a_t")
    Listlinker = []
    # List<WebElement> rows = wholeTable.find_element_by_class_name("gsc_a_tr")
    # file = open("output", "w")
    Listlinker = wholeTable.find_elements_by_xpath("//a[@class='gsc_a_at']")
    # file.write(scholarPage.prettify())
    # file.close()
    # table = scholarPage.find('table', id="gsc_a_t")
    # rows = table.tbody.find_all('tr', class_="gsc_a_tr")
    print "Total paper is: ", len(Listlinker)
    URLs = []
    i = paper_begin
    for link in Listlinker:
        # href = link.getAttribute("css=a@href")
        temp = link.get_attribute("href")
        print type(temp)
        print temp
        URLs.append(str(temp))
        # URLs = temp
    if paper_end > len(Listlinker):
        print "exceed total paper number"
    if paper_begin < 1:
        print "paper start at least 1"
    print paper_begin,paper_end
    for i in range(int(paper_begin), int(paper_end)+1):
        URL = URLs[i-1]
        print "Paper URL is ", URL
        BibTeXfromURL(URL)
        print "Paper ", i , "finished"
    # for i in range(len(URLs)):
    #     URL = URLs[i]
    #     print "Paper URL is ", URL
    #     BibTeXfromURL(URL)
    #     print "Paper ", i , "finished"



    # # print rows[0]
    # paperURL = rows[0].findAll('a')[0]['href']
    # URL = "https://scholar.google.com" + paperURL

    # # chrome_browser.find_element_by_link_text(paperName).click()
    # chrome_browser.get(URL)
    # # get BibTex
    # # get drop menu first
    # download_menu = chrome_browser.find_element_by_id("gsc_btn_exp-bd")
    # download_menu.click()
    # # select export as BibTex
    # bibitem = download_menu.find_element_by_xpath("//div[@class='gs_md_se gs_vis']")
    # item = bibitem.find_element_by_xpath("//li[contains(text(), 'BibTeX')]")
    # item.click()

    # # save the BibTeX to file
    # prune = BeautifulSoup(chrome_browser.page_source)
    # with open("BibTeX","a") as myfile:
    #     myfile.write(prune.find('pre').text)

    # chrome_browser.close()
