# -*- coding: utf-8 -*-

# ABrCrawl: Crawl pages from Agencia Brasil's images repository webpage
# and copy the data to a structured database.
#
# http://github.com/fczuardi/abrcrawl
#
# Copyright (c) 2009, Fabricio Zuardi
# All rights reserved.
#  
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of the author nor the names of its contributors
#     may be used to endorse or promote products derived from this
#     software without specific prior written permission.
#  
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__author__ = ('Fabricio Zuardi', 'fabricio@fabricio.org', 'http://fabricio.org')
__license__ = "BSD"

import sys
import getopt
import re
import urllib2
import csv
import simplejson as json

#CONSTANTS
AGENCIA_BRASIL_GALLERY_URL = "http://www.agenciabrasil.gov.br/imagens/banco_de_imagens_view/lista"
AGENCIA_BRASIL_PAGINATION_PARAM = "b_start:int"
AGENCIA_BRASIL_PAGE_SIZE = 15
OUTPUT_FORMATS = ['csv','json']

#GLOBAL FLAGS
verbose = None

# response = urllib2.urlopen("http://www.acme.com/tables.html")

def usage():
  print """
ABrCrawl v.0.1 (thackday)
http://github.com/fczuardi/abrcrawl

Crawl pages from Agencia Brasil's image bank webpage and output the contents as
tabular data.

Parameters:
  -h, --help:\t\tPrint this message.
  -d, --date:\t\tA starting date in the YYYY/MM/DD format.
  -p, --pages:\t\tThe number of pages to retrieve (ABr uses %s images per page)
  -f, --format:\t\tThe output format. Available formats: %s
  -i, --indent:\t\tIf output format can be pretty printed(json for example) use the number of white spaces to use as indent level.
  -o, --output-file:\tSave the output to a given filename.
  -v, --verbose:\tPrint extra info while performing the tasks.
""" % (AGENCIA_BRASIL_PAGE_SIZE, ', '.join(OUTPUT_FORMATS))

def main():
  global verbose
  start_date = None
  page_total = 1
  results_format = 'csv'
  table = []
  output_file = sys.stdout
  indent_level = None
  if(len(sys.argv) < 2):
    return usage()
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hd:p:vf:o:i:", ["help", "date=", "pages=", "verbose", "format=", "output-file=", "indent="])
  except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)
  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    elif o in ("-d", "--date"):
      start_date = a
    elif o in ("-p", "--pages"):
      page_total = int(a)
    elif o in ("-v", "--verbose"):
      verbose = True
    elif o in ("-f", "--format"):
      results_format = a
    elif o in ("-o", "--output-file"):
      output_file = file( a, "wb" )
    elif o in ("-i", "--indent"):
      indent_level = int(a)
    else:
      assert False, "unhandled option"
  for i in range(1,page_total+1):
    log("Getting page %s" % i)
    content = get_page(i, start_date)
    if content:
      table.extend(extract_data(content))
    else:
      print "No data."
  print_results(table,results_format,output_file, indent_level)
  output_file.close()
  


"""Load the contents of a web page. Returns False if error or the content if success.
"""
def get_page(page_num, start_date=None):
  log("Start date:%s" % start_date)
  date_range = "getDataPublicacao:date:list=%s+23:59:59&getDataPublicacao_usage=range:max" % (start_date) if start_date else ''
  start = AGENCIA_BRASIL_PAGE_SIZE * page_num - AGENCIA_BRASIL_PAGE_SIZE
  gallery_url = "%s?%s&%s=%s" % (AGENCIA_BRASIL_GALLERY_URL, date_range, AGENCIA_BRASIL_PAGINATION_PARAM, start)
  log("Acessing %s\t" % gallery_url)
  try:
    f = urllib2.urlopen(gallery_url)
    content = f.read()
    log("Success.")
    return content;
  except urllib2.HTTPError, e:
    if e.code == 401:
      log('Not authorized.')
    elif e.code == 404:
      log('Page not found.')
    elif e.code == 503:
      log('Service unavailable.')
    else:
      log('Unknown error: ')
  except urllib2.URLError, e:
    log("Error %s" % e.reason)
  return False

def extract_data(html, date='unknown'):
  photos = []
  last_date = date
  while 1:
    image_entry_pattern = '<div id="lista_banco_imagens_bloco">.*?<a href="([^"]*)".*?<img src="([^"]*)".*?<div class="nomeFotografo">(.*?)</div>.*?<block align="left" class="legendafoto2">(.*?)</block>'
    matches = re.search(image_entry_pattern, html, re.S|re.M)
    if matches:
      text_before_match = matches.string[:matches.start(0)]
      date_mark_pattern = 'class="chapeu1".*?>(.*?)<'
      last_date_mark_matches = re.search(date_mark_pattern, text_before_match, re.S|re.M)
      if last_date_mark_matches:
        last_date = last_date_mark_matches.group(1)
      photos.append({
        'thumbnail_url' : matches.group(2),
        'author' : matches.group(3),
        'description' : matches.group(4),
        'pub_day' : last_date,
        'photo_page' : matches.group(1),
      })
      html = matches.string[matches.end(4):]
    else: #no more matches
      break
  return photos

def print_results(table, fmt, output_file, indent):
  if fmt == 'csv':
    keys = table[0].keys()
    #write header
    output_file.write("%s\n" % ','.join(keys))
    #write rows
    writer = csv.DictWriter(output_file, keys)
    writer.writerows(table)
  elif fmt == 'json':
    output = json.dumps(table,indent=indent)
    output_file.write(output)
  else:
    print str(table)
  
def log(m):
  if verbose: print(m)
  
if __name__ == "__main__":
  main()