#!/usr/bin/env python
# ~*~ coding: utf-8 ~*~
import json
import csv
import os
import shutil
import time
import re
import zipfile
from pprint import pprint

NOW = int(time.time())
PREFER_COLOR=True
CSV_PATH="../../res/list.csv"
PICTOS_DIR_PATH="../../res/images"

def sanitize_string( string ):
    if type(string) is not unicode:
        string = unicode(string, encoding='utf-8')

    string = re.sub(u"[àáâãäå]", 'a', string)
    string = re.sub(u"[èéêë]", 'e', string)
    string = re.sub(u"[ìíîï]", 'i', string)
    string = re.sub(u"[òóôõö]", 'o', string)
    string = re.sub(u"[ùúûü]", 'u', string)
    string = re.sub(u"[ýÿ]", 'y', string)
    string = re.sub(u"[ç]", 'c', string)
    string = re.sub(u"[\s]", '_', string)

    return string.encode('ascii', 'ignore')

def create_output_folders( folder ):
    if not os.path.exists( "output" ):
        os.mkdir("output")
    path = "output/" + sanitize_string(folder)
    if os.path.exists( path ):
        shutil.rmtree( path )
    os.mkdir( path )
    os.mkdir( path + "/medias" )
    return path

def name_with_meta( picto ):
    name = picto['name'] + " ("+ picto['meta'] +")";
    if PREFER_COLOR:
        if picto['color'] == 1:
            name = name + " couleur"
    else:
        if picto['bw'] == 0:
            name = name + " couleur"
    name = name + ".jpg"
    return name

def name_without_meta( picto ):
    name = picto['name'];
    if PREFER_COLOR:
        if picto['color'] == 1:
            name = name + " couleur"
    else:
        if picto['bw'] == 0:
            name = name + " couleur"
    name = name + ".jpg"
    return name

def copy_picto( picto, newname, output_dir, src_dir ):
    name = picto['name'];
    if picto['meta'] != "":
        name = name_with_meta( picto )
        if not os.path.isfile( src_dir + "/" + name ):
            name = name_without_meta( picto )
    else:
        name = name_without_meta( picto )

    orig = src_dir + "/" + name
    output = output_dir+"/medias/"+ newname + ".jpg"

    shutil.copyfile( orig, output )

def write_definition( data, output_dir ):
    print("Writing "+output_dir+"/definition.json")
    with open( output_dir+"/definition.json", "w") as output:
        json.dump( data, output )

def archive_folder( folder, labelgroup ):
    print( 'Zipping into '+folder+'/'+labelgroup + '.zip' )
    os.chdir( folder )
    zipf = zipfile.ZipFile( labelgroup + '.zip', 'w', zipfile.ZIP_DEFLATED)
    zipf.write('definition.json')
    for root, dirs, files in os.walk( 'medias' ):
        for file in files:
            zipf.write( os.path.join( 'medias', file ) )
    zipf.close()
    os.chdir( '../..' )

def gen_archive( filename, group = None ):
    
    labelgroup = "all" if group == None else group 
    
    print ("Generation of archive '"+labelgroup+"'")

    output = create_output_folders( labelgroup )
    data = {
        "meta": {},
        "pictos" : [],
        "groups" : [],
        "links" : []
    }
    data['meta'] = {
            "version": NOW,
            "packageFormat": 2,
            "label": "Picto Bailly - " + labelgroup,
            "name": "org.eu.nveo.bailly."+sanitize_string(labelgroup),
            "nbpictos": 0,
            "nbgroups": 0
    }

    #pprint( data )

    links = {}
    groups = {}

    with open( filename, 'rb') as csvfile:
        reader = csv.reader( csvfile, delimiter="," )
        # skip the first line
        reader.next()
        prev = {
            "name": "",
            "group": "",
            "meta": "",
            "bw": 0,
            "color": 0,
            "id": -1
        }
        idpicto=0
        idgroup=0
        for row in reader:

            picto = {
                "name": row[2],
                "group": row[3],
                "meta": row[4],
                "bw": int(row[0]),
                "color": int(row[1]),
                "id": idpicto
            }

            isref = int( row[6] )


            if group == None or group == picto['group']:

                if picto['group'] not in links.keys():
                    links[ picto['group'] ] = { "group": picto['group'], "pictos": [], 'picto': 0 }

                links[ picto['group'] ]['pictos'].append( picto['id'] )
                if isref == 1:
                    links[picto['group']]['picto'] = picto['id']
        
                if picto['name'] != prev['name'] or picto['meta'] != prev['meta']:
                    data["pictos"].append( {
                        "label": picto['name'] ,
                        "meta": picto['meta'],
                        "image": str(idpicto) + ".jpg",
                        "audio": "null",
                        "id": idpicto
                    })
                    copy_picto( picto, str(idpicto), output, PICTOS_DIR_PATH )
                    idpicto = idpicto + 1

            prev = picto

        for group in links.keys():
            data['links'].append( { 
                "group": group,
                "pictos": links[group]['pictos']
            } )
            data['groups'].append( { 
                'label': group,
                'picto': links[group]['picto']
            } )

    nbpictos = len( data['pictos'] )
    data['meta']['nbpictos'] = nbpictos
    nbgroups = len( data['groups'] )
    data['meta']['nbgroups'] = nbgroups
    print( str( nbpictos ) + " pictos")

    write_definition( data, output )

    archive_folder( output, data['meta']['name'] )
    print("")

def list_groups( filename ):
    groups = {};
    with open( filename, 'rb') as csvfile:
        reader = csv.reader( csvfile, delimiter="," )
        reader.next()
        for row in reader:
            csvgroup = row[3]
            if csvgroup != "":
                groups[csvgroup] = 1;
    return groups.keys();

groups = list_groups( CSV_PATH );

for group in groups:
    gen_archive( CSV_PATH , group )

gen_archive( CSV_PATH, None )
