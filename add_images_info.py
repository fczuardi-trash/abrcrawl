# -*- coding: utf-8 -*-

# AddImagesInfo: Run through a local directory of downloaded images and update
# a cvs from ABrCrawl to include information about the files, such as size, 
# dimensions, width and height.
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
import os
from PIL import Image
from PIL.ExifTags import TAGS

#GLOBAL FLAGS
verbose = None

#CONSTANTS
AGENCIA_BRASIL_IMAGES_FOLDER = "http://www.agenciabrasil.gov.br/media/imagens/"
AGENCIA_BRASIL_VIEW_POSTFIX = "/view"

def usage():
  print """
AddImagesInfo v.0.1
http://github.com/fczuardi/abrcrawl

Run through a local directory of downloaded images and update a cvs generated
by ABrCrawl to include information about the files, such as size, dimensions, 
width and height.

Parameters:
  -h, --help:\t\tPrint this message.
  -i, --input-file:\tThe ABrCrawl generated csv file to be used as input.
  -d, --images-dir:\tThe directory where the image files are.
  -o, --output-file:\tFile where to save the updated csv.
  -c, --curl-config-file:\tFile to store a curl config with th URLs for missing and corrupted images.
  -v, --verbose:\tPrint extra info while performing the tasks.
"""


def updateRow(row, img, img_path):
  photo_format = img.format
  photo_width = img.size[0]
  photo_height = img.size[1]
  photo_orientation = 'landscape' if photo_width > photo_height else 'portrait'
  photo_size = os.path.getsize(img_path)
  exif_artist = ''
  exif_flash = ''
  exif_date_time_original = ''
  exif_make = ''
  exif_model = ''
  exif_software = ''
  exif_info = None
  try:
    exif_info = img._getexif()
  except Exception as e:
    pass
  if exif_info:
    for tag, value in exif_info.items():
      decoded = str(TAGS.get(tag, tag))
      value = str(value).strip()
      if decoded == 'DateTimeOriginal': exif_date_time_original = value
      if decoded == 'Make': exif_make = value
      if decoded == 'Model': exif_model = value
      if decoded == 'Flash': exif_flash = value
      if decoded == 'Software': exif_software = value
      if decoded == 'Artist': exif_artist = value
  new_row = {
    'pub_day':row['pub_day'],
    'thumbnail_url':row['thumbnail_url'],
    'photo_page':row['photo_page'],
    'description':row['description'],
    'author':row['author'],
    'photo_format':photo_format, 
    'photo_orientation':photo_orientation, 
    'photo_width':photo_width, 
    'photo_height':photo_height, 
    'photo_size':photo_size,
    'exif_artist':exif_artist, 
    'exif_flash':exif_flash, 
    'exif_date_time_original':exif_date_time_original, 
    'exif_make':exif_make, 
    'exif_model':exif_model, 
    'exif_software':exif_software
  }
  return new_row

def main():
  global verbose
  output_file = sys.stdout
  curl_config_file = None
  if(len(sys.argv) < 2):
    return usage()
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:d:o:c:v", ["help", "input-file=", "images-dir=", "output-file=", "curl-config-file", "verbose"])
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
    elif o in ("-d", "--images-dir"):
      images_dir = a
    elif o in ("-o", "--output-file"):
      output_file = file( a, "wb" )
    elif o in ("-c", "--curl-config-file"):
      curl_config_file = open( a, "wb" )
    elif o in ("-v", "--verbose"):
      verbose = True
    else:
      assert False, "unhandled option"
  new_table = []
  not_found_files = []
  corrupted_images = []
  passed_rows = []
  rows_updated = 1
  duplicated_rows = 0
  input_reader = csv.DictReader(input_file)
  ignore_url_until = len(AGENCIA_BRASIL_IMAGES_FOLDER)
  ignore_url_after = len(AGENCIA_BRASIL_VIEW_POSTFIX)
  #copy csv data to the new table
  log('reading input csv file…')
  #look for the image files in the --images-dir and update the rows with new columns
  log('retrieving local images info…')
  for row in input_reader:
    if row in passed_rows:
      duplicated_rows = duplicated_rows + 1
      continue
    passed_rows.append(row)
    abr_filename = row['photo_page'][ignore_url_until:-ignore_url_after]
    local_filename = abr_filename.replace('/','_')
    image_path = "%s/%s" % (images_dir,local_filename)
    #first row or empty row or empty image url, skip
    if local_filename == '': continue
    #there is no local copy for the image, update the not found image list
    if not os.path.exists(image_path):
      not_found_files.append(abr_filename)
      continue
    #local file exists, try to open it
    try:
      img = Image.open(image_path)
      new_table.append(updateRow(row, img, image_path))
      rows_updated = rows_updated + 1
    #local file is corrupted, updated corrupted list
    except IOError as e:
      corrupted_images.append(abr_filename)
  #info about some images could not be retrieved, generate a curl config file for the user to download the missing images
  if curl_config_file and (len(not_found_files)>0 or len(corrupted_images) > 0):
    curl_config = ''
    log('%s files missing.' % len(not_found_files))
    for filename in not_found_files:
      curl_config = curl_config + 'url = "%s%s"\noutput = "%s"\n' % (AGENCIA_BRASIL_IMAGES_FOLDER, filename, filename.replace('/','_'))
    log('%s files corrupted.' % len(corrupted_images))
    for filename in corrupted_images:
      curl_config = curl_config + 'url = "%s%s"\noutput = "%s"\n' % (AGENCIA_BRASIL_IMAGES_FOLDER, filename, filename.replace('/','_'))
    curl_config_file.write(curl_config)
  print_results(new_table,output_file)
  # log(new_table)
  log('Update finished. %s rows updated, %s duplicated rows ignored, %s files missing, %s files corrupted.' % (rows_updated, duplicated_rows, len(not_found_files), len(corrupted_images)))

def print_results(table, output_file):
  keys = [
    'pub_day',
    'thumbnail_url',
    'photo_page',
    'description',
    'author',
    'photo_format', 
    'photo_orientation', 
    'photo_width', 
    'photo_height', 
    'photo_size',
    'exif_artist', 
    'exif_flash', 
    'exif_date_time_original', 
    'exif_make', 
    'exif_model', 
    'exif_software'
  ]
  #write header
  output_file.write("%s\n" % ','.join(keys))
  #write rows
  writer = csv.DictWriter(output_file, keys, quoting=csv.QUOTE_ALL)
  writer.writerows(table)
  return True

def log(m):
  global verbose
  if verbose: print(m)
  
if __name__ == "__main__":
  main()