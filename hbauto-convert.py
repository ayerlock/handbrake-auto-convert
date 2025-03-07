#!/usr/bin/env python3

import argparse
import logging
import os
import re
import subprocess
import sys

from pathlib import Path
from pprint import pprint
from pymediainfo import MediaInfo

###------------------------------------------------------------------------------------------------------------------------------

def initlogging( args ):
	logger										  = logging.getLogger( __name__ )

	loglevels= {'crit':logging.CRITICAL,
				'error':logging.ERROR,
				'warn':logging.WARNING,
				'info':logging.INFO,
				'debug':logging.DEBUG }

	loglevel = loglevels.get( args.loglevel, logging.NOTSET )
	logger.setLevel( loglevel )
	logformat = '(%(asctime)-11s)  :%(levelname)-9s:%(funcName)-13s:%(message)s'

	if ( len( logger.handlers ) == 0 ):
		try:
			colorize									= __import__( 'logutils.colorize', fromlist = ['colorize'] )
			console_handler								= colorize.ColorizingStreamHandler()
			console_handler.level_map[logging.DEBUG]	= ( None, 'blue', False )
			console_handler.level_map[logging.INFO]		= ( None, 'green', False )
			console_handler.level_map[logging.WARNING]	= ( None, 'yellow', False )
			console_handler.level_map[logging.ERROR]	= ( None, 'red', False )
			console_handler.level_map[logging.CRITICAL]	= ( 'red', 'white', False )
		except ImportError:
			console_handler = logging.StreamHandler()
	else:
		console_handler  = logging.StreamHandler()

	console_handler.setFormatter( logging.Formatter( logformat, datefmt = '%I:%M:%S %p' ) )

	if args.logfile is not None:
		file_handler = logging.FileHandler( args.logfile )
		file_handler.setFormatter( logging.Formatter( logformat, datefmt = '%I:%M:%S %p' ) )
		logger.addHandler( file_handler )

	logger.addHandler( console_handler )

###------------------------------------------------------------------------------------------------------------------------------

class fulldict( dict ):
	def __init__( self, **kwargs ):
		keys										= kwargs.keys()
		for key in keys:
			self[key]							   = kwargs[key]

	def __getattr__( self, key ):
		return self[key]

	def __hasattr__( self, key ):
		if self.has_key( key ):
			return True
		else:
			return False

	def __setattr__( self, key, value ):
		self[key] = value

###------------------------------------------------------------------------------------------------------------------------------

def get_disc_info( path ):
	logger = logging.getLogger( __name__ )
	print( "" )

	dvdinfo = fulldict()
	
	command = [
				"E:\\Handbrake\\HandBrakeCLI.exe",
				"-i", path,
				"--scan"
			]
	logger.info( "  Scanning Disc: %s" % path )
	logger.debug( "    Scan Command: %s" % command )
	data = scan_output( command, "scan: DVD has" )

	logger.debug( "\t ISO Scanning:" )
	logger.debug( "\t\tData: %s" % data )

	titles = data.split( ":" )[3].strip()
	#logger.debug( "\t	Titles[1]: %s" % titles )

	titles = titles.split( " " )[2].strip()
	#logger.debug( "\t	Titles[2]: %s" % titles )

	fname = os.path.basename( path ).strip ()
	#logger.debug( "\t	Filename: %s" % fname )

	name = fname.split( "." )[0].strip()
	#logger.debug( "\t	Name: %s" % name )

	dvdinfo.name = name
	dvdinfo.path = path
	dvdinfo.titlecount = titles
	dvdinfo.type = "iso"

	return dvdinfo

###------------------------------------------------------------------------------------------------------------------------------

def get_dvd_info( path ):
	logger = logging.getLogger( __name__ )

	dvdinfo = fulldict()
	
	command = [
				"E:\\Handbrake\\HandBrakeCLI.exe",
				"-i", path,
				"--scan"
			]
	logger.info( "  Scanning DVD: %s" % path )
	logger.debug( "    Scan Command: %s" % command )
	data = scan_output( command, "scan: DVD has" )

	titles = data.split( ":" )[3].strip()
	#logger.debug( "\t	Titles[1]: %s" % titles )

	titles = titles.split( " " )[2].strip()
	#logger.debug( "\t	Titles[2]: %s" % titles )

	name = os.path.split( os.path.split( path )[0] )[1]
	#logger.debug( "\t	Name: %s" % name )

	dvdinfo.name = name
	dvdinfo.path = path
	dvdinfo.titlecount = titles
	dvdinfo.type = "videots"

	return dvdinfo

###------------------------------------------------------------------------------------------------------------------------------

def get_video_info( video_file ):
	logger = logging.getLogger( __name__ )

	videoinfo = fulldict()

	# Get the video information using MediaInfo.
	videoinfo.path = path
	media_info = MediaInfo.parse( video_file )
	for track in media_info.tracks:
		if track.track_type == "Video":
			videoinfo.format = track.format
			videoinfo.rawduration = track.duration
			videoinfo.duration = track.other_duration[2]
			videoinfo.height = track.height
			videoinfo.width = track.width

	return videoinfo

###------------------------------------------------------------------------------------------------------------------------------

def find_media_objects( args, directory, depth, findtype, extensions ):
	logger = logging.getLogger( __name__ )

	if findtype == 'file':
		# Recursively find all video files in the given directory.
		media_objects = []
		for root, subdirs, files in os.walk( directory ):
			if depth is not None:
				current_depth = root[len( directory ):].count( os.sep )
				if current_depth > depth:
					continue

			for file in files:
				if file.lower().endswith( extensions ):
					filepath = os.path.join( root, file )
					media_objects.append( filepath )

	elif findtype == 'dir':
		# Recursively find all dvd directories in the given root.
		media_objects = []
		for root, subdirs, files in os.walk( directory ):
			if depth is not None:
				current_depth = root[len( directory ):].count( os.sep )
				if current_depth > depth:
					continue

			for subdir in subdirs:
				if subdir == extensions:
					dirpath = os.path.join( root, subdir )
					media_objects.append( dirpath )

	return media_objects

###------------------------------------------------------------------------------------------------------------------------------

def print_media( items, mediatype ):
	logger = logging.getLogger( __name__ )

	if mediatype == 'file':
		for item in items:
			if item.lower().endswith( ".iso" ):
				logger.info( "  Scanning Packed DVD: %s" % item )
				name = os.path.split( os.path.split( item )[0] )[1]
				videoinfo = get_dvd_info( item )
				videoinfo.name = name
			else:
				logger.info( "  Scanning File: %s" % item )
				videoinfo = get_video_info( item )
				logger.debug( "\tFile: %s" % item )
				logger.debug( "\t\tFormat: %s" % videoinfo.format )
				logger.debug( "\t\tDuration: %s" % videoinfo.duration )
				logger.debug( "\t\tResolution: %s x %s" % ( videoinfo.width, videoinfo.height ) )

	elif mediatype == 'dir':
		for item in items:
			logger.info( "  Scanning Unpacked DVD: %s" % item )
			name = os.path.split( os.path.split( item )[0] )[1]
			videoinfo = get_dvd_info( item )
			videoinfo.name = name

###------------------------------------------------------------------------------------------------------------------------------

def convert_videos( video_files, handbrake_profile ):
	logger = logging.getLogger( __name__ )

	# Convert each video file using HandBrakeCLI with the given profile.
	for video_file in video_files:
		output_file = os.path.splitext( video_file )[0] + "_converted.mp4"
		command = [
			"HandBrakeCLI",
			"-i", video_file,
			"-o", output_file,
			"--preset-import-file", handbrake_profile
		]
		#subprocess.run( command, check=True )

###------------------------------------------------------------------------------------------------------------------------------

def find_packed_dvd( args ):
	logger = logging.getLogger( __name__ )

	extensions = ( ".iso" )
	findtype = ( 'file' )

	# Find DVD Files
	dvd_files = find_media_objects( args, args.directory, args.depth, findtype, extensions )
	if not dvd_files:
		logger.warning( "No dvd files found in the specified directory." )
		logger.warning( "" )
		#return

	#print_media( dvd_files, findtype )

	return dvd_files

###------------------------------------------------------------------------------------------------------------------------------

def find_unpacked_dvd( args ):
	logger = logging.getLogger( __name__ )

	directory = "VIDEO_TS"
	findtype = ( 'dir' )

	# Find DVD Directories
	dvd_dirs = find_media_objects( args, args.directory, args.depth, findtype, directory )
	if not dvd_dirs:
		logger.warning( "\tNo dvd directories found in the specified root." )
		logger.warning( "" )
		#return

	#print_media( dvd_dirs, findtype )

	return dvd_dirs

###------------------------------------------------------------------------------------------------------------------------------

def find_videos( args ):
	logger = logging.getLogger( __name__ )

	extensions = ( ".3gp", ".asf", ".avi", ".divx", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".mts", ".rm", ".ts", ".wmv" )
	findtype = ( 'file' )

	# Find Video Files
	video_files = find_media_objects( args, args.directory, args.depth, findtype, extensions )
	if not video_files:
		logger.warning( "No video files found in the specified directory." )
		logger.warning( "" )
		#return

	#print_media( video_files, findtype )

	return video_files

###------------------------------------------------------------------------------------------------------------------------------

def scan_output( command, search ):
	logger = logging.getLogger( __name__ )

	try:
		process = subprocess.run(command, capture_output=True, text=True, check=True)
		count = 0
		for line in process.stderr.splitlines():
			if search in line:
				count += 1
				output = line
		if count != 1:
			output = False
	except subprocess.CalledProcessError as e:
		print(f"Command execution failed: {e}")
		output = False
	except FileNotFoundError:
		print(f"Command not found")
		output = False

	return output

###------------------------------------------------------------------------------------------------------------------------------

def dischandler( args, profile ):
	logger = logging.getLogger( __name__ )

	print( "" )
	print( "" )
	if args.disc and args.dvd:
		logger.info( "Scanning for both packed and unpacked DVDs" )
		discs = find_packed_dvd( args )
		for disc in discs:
			logger.debug( "Disc:\t %s" % disc )
		dvds = find_unpacked_dvd( args )
		for dvd in dvds:
			logger.debug( "DVD:\t %s" % dvd )
			discs.append( dvd )

	elif args.disc and not args.dvd:
		logger.info( "Scanning for packed DVDs" )
		discs = find_packed_dvd( args )

	elif not args.disc and args.dvd:
		logger.info( "Scanning for unpacked DVDs" )
		discs = find_unpacked_dvd( args )

	if discs is not None:
		for dvd in discs:
			print( "" )
			print( "" )
			if dvd.lower().endswith( "iso" ):
				logger.debug( "Calling: get_disc_info( %s )" % dvd )
				dvdinfo = get_disc_info( dvd )
				logger.info( "" )
				for key, value in dvdinfo.items():
					logger.debug( "DVD:\t %s\tKey: %s\tValue: %s" % ( dvdinfo.name, key, value ) )
				#logger.debug( "Disc:\t %s\tKey: %s" % ( dvd, dvdinfo ) )
			else:
				logger.debug( "Calling: get_dvd_info( %s )" % dvd )
				dvdinfo = get_dvd_info( dvd )
				logger.info( "" )
				for key, value in dvdinfo.items():
					logger.debug( "DVD:\t %s\tKey: %s\tValue: %s" % ( dvdinfo.name, key, value ) )

			basepath = os.path.split( dvdinfo.path )[0]
			for title in range( 1, ( int( dvdinfo.titlecount ) + 1 ) ):
				newfile = ( "%s-%s.mp4" % ( dvdinfo.name, title ) )
				newpath = os.path.join( basepath, newfile )
				command = [
					"E:\\Handbrake\\HandBrakeCLI.exe",
					"-i", dvdinfo.path,
					"-o", newpath,
					"--preset-import-file", os.path.join( profile.path, profile.file ),
					"-Z", profile.name,
					"--title", str( title )
				]
				logger.info( command )
				if args.run:
					if not os.path.isfile( newpath ):
						subprocess.run( command, check=True )
					else:
						logger.error( "File already exists: %s" % newpath )

	#HandBrakeCLI.exe -i D:\Videos\dvds\ProballDisc2\VIDEO_TS -o ProballDisc2-01.mp4 --preset-import-file x265-mp4-dvd-main.json -Z "(x265) Convert MP4 - DVD Main"

###------------------------------------------------------------------------------------------------------------------------------

def vidhandler( args, profile, profilehq ):
	logger = logging.getLogger( __name__ )

	if args.videos:
		video_files = find_videos( args )
		logger.info( "Printing Video Info" )
		for video in video_files:
			videoinfo = get_video_info( video )
			if args.print:
				print( "File:\t %s\t\tInfo: %s" % ( video, videoinfo ) )

###------------------------------------------------------------------------------------------------------------------------------

def convert_dvd( path, profile ):
	logger = logging.getLogger( __name__ )

	# Convert DVD using HandBrakeCLI with the given profile.
	for video_file in video_files:
		output_file = os.path.splitext( video_file )[0] + "_converted.mp4"
		command = [
			"HandBrakeCLI",
			"-i", video_file,
			"-o", output_file,
			"--preset-import-file", handbrake_profile
		]
		#print( f"Converting: {video_file} -> {output_file}" )
		#subprocess.run( command, check=True )

###------------------------------------------------------------------------------------------------------------------------------

def main():
	### Command Line Arguments ###-----------------------------------------------------------------------------------------------
	parser = argparse.ArgumentParser( description = 'HandbrakeCLI encoding automation engine.', prog = os.path.basename( re.sub( ".py", "", sys.argv[0] ) ) )
	gparser = parser.add_argument_group( 'standard functionality' )
	gparser.add_argument( "-d",	"--directory",	required = False,			default = '.',		help = "Directory to search for video files" )
	gparser.add_argument( "-n",	"--depth",		required = False,			type = int,			help = "Search depth below [DIRECTORY]" )
	gparser.add_argument(		"--disc",		action = 'store_true',		default = False,	help = "Enable scanning for DVD ISO files" )
	gparser.add_argument(		"--dvd",		action = 'store_true',		default = False,	help = "Enable scanning for unpacked DVDs [VIDEO_TS]" )
	gparser.add_argument(		"--videos",		action = 'store_true',		default = False,	help = "Enable scanning for non HEVC video files" )
	gparser.add_argument(		"--run",		action = 'store_true',		default = False,	help = "Enable conversion processing" )
	#gparser.add_argument( "-p",	"--print",		action = 'store_true',		default = False )
	gparser = parser.add_argument_group( 'logging' )
	gparser.add_argument(       '--loglevel',       action = 'store',       dest = "loglevel",  metavar = "[loglevel]",    default = 'info',   choices= ['crit', 'error', 'warn', 'notice', 'info', 'verbose', 'debug', 'insane'] )
	gparser.add_argument(       '--logfile',        action = 'store',       dest = "logfile",   metavar = "[logfile]" )
	gparser.add_argument( '-v', '--verbose',        action = 'count',       default = 0 )
	args = parser.parse_args()
	###--------------------------------------------------------------------------------------------------------------------------

	initlogging( args )
	logger = logging.getLogger( __name__ )

	hbprofile = fulldict()
	hbprofile.path = "E:\\Handbrake\\"
	hbprofile.file = "x265-mp4-dvd-main.json"
	hbprofile.name = "(x265) Convert MP4 - DVD Main"

	hbprofilehq = fulldict()
	hbprofilehq.path = "E:\\Handbrake\\"
	hbprofilehq.file = "x265-mp4-hq-main.json"
	hbprofilehq.name = "(x265) Convert MP4 - HQ Main"

	if not os.path.isfile( os.path.join( hbprofile.path, hbprofile.file ) ):
		logger.error( "Error: The specified HandBrake profile file does not exist." )
	else:
		logger.info( "Found Handbrake Profile: %s" % hbprofile.file )
	if not os.path.isfile( os.path.join( hbprofilehq.path, hbprofilehq.file ) ):
		logger.error( "Error: The specified HandBrake profile file does not exist." )
	else:
		logger.info( "Found Handbrake Profile: %s" % hbprofilehq.file )

	# List of dvd/video file extensions to search for
	
	print( "" )
	dischandler( args, hbprofile )
	print( "" )
	#dischandler( args, hbprofile )
	#print( "" )
	vidhandler( args, hbprofile, hbprofilehq )
	print( "" )

	#   return
	#convert_videos( video_files, args.profile )

###------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
	main()
