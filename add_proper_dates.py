# -*- coding: utf-8 -*-

# AddProperDates: Update a cvs from ABrCrawl to include creation date
# and modified date columns by going through all individual pages urls and 
# scraping that extra info.
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
import csv
import urllib2
import re
import os

#GLOBAL FLAGS
verbose = None

def usage():
  print """
AddProperDates
http://github.com/fczuardi/abrcrawl

Update a cvs from ABrCrawl to include creation date and modified date columns 
by going through all individual pages urls and scraping that extra info.

Parameters:
  -h, --help:\t\tPrint this message.
  -i, --input-file:\tThe ABrCrawl generated csv file to be used as input.
  -o, --output-file:\tFile where to save the updated csv.
  -v, --verbose:\tPrint extra info while performing the tasks.
"""

def main():
  global verbose
  output_file = sys.stdout
  if(len(sys.argv) < 2):
    return usage()
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:o:v", ["help", "input-file=", "output-file=", "verbose"])
  except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)
  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    elif o in ("-i", "--input-file"):
      input_file = file( a, "r" )
    elif o in ("-o", "--output-file"):
      output_file = file( a, "wb" )
    elif o in ("-v", "--verbose"):
      verbose = True
    else:
      assert False, "unhandled option"
  input_reader = csv.DictReader(input_file)
  new_table = []
  keys = input_reader.fieldnames
  new_keys = keys[:]
  new_keys.extend(['created_date', 'updated_date'])
  for row in input_reader:
    log('Line #%s.' % (input_reader.line_num-1))
    url = row['photo_page']
    page_content = get_page_contents(url)
    dates = extract_abr_date_string(page_content)
    log(dates)
    pass

def get_page_contents(url):
  log("Acessing %s\t" % url)
  try:
    f = urllib2.urlopen(url)
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

def extract_abr_date_string(html):
  date_pattern = '<div class="documentByLine">.*?<span>.*?([0-9]+) de (.*?) de ([0-9]+) - (..)h(..).*?</span>.*?</span>.*?([0-9]+) de (.*?) de ([0-9]+) - (..)h(..)'
  matches = re.search(date_pattern, html, re.S|re.M)
  if matches:
    created_date_day = matches.group(1)
    created_date_month = matches.group(2)
    created_date_year = matches.group(3)
    created_date_hour = matches.group(4)
    created_date_minute = matches.group(5)
    updated_date_day = matches.group(6)
    updated_date_month = matches.group(7)
    updated_date_year = matches.group(8)
    updated_date_hour = matches.group(9)
    updated_date_minute = matches.group(10)
    months = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    for i in range(0,12):
      created_date_month = re.sub(months[i], str(i+1), created_date_month)
      updated_date_month = re.sub(months[i], str(i+1), updated_date_month)
    return [
              ('%d-%02d-%02dT%02d:%02d-03:00' % (int(created_date_year), int(created_date_month), int(created_date_day), int(created_date_hour), int(created_date_minute))),
              ('%d-%02d-%02dT%02d:%02d-03:00' % (int(updated_date_year), int(updated_date_month), int(updated_date_day), int(updated_date_hour), int(updated_date_minute)))
            ]
  else:
    log('no matches')
  
def extract_abr_cloudwords(html):
  #                                 <div id="cloudwords" class="assuntos1">
  #                                     
  #                                         <a
  # href="http://www.agenciabrasil.gov.br/assunto_view/Congresso Nacional"
  # style="font-size: 100%; font-color: #6C7962; !important">Congresso Nacional</a>
  #                                     
  #                                     
  #                                         <a
  # href="http://www.agenciabrasil.gov.br/assunto_view/movimentos sociais"
  # style="font-size: 100%; font-color: #6C7962; !important">movimentos sociais</a>
  #                                     
  #                                 </div>
  # 

def log(m):
  global verbose
  if verbose: print(m)
  
if __name__ == "__main__":
  main()