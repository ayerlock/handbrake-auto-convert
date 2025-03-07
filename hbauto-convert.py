#!/usr/bin/env python3

import os
import argparse
import subprocess
import sys

from pathlib import Path
from pprint import pprint
from pymediainfo import MediaInfo

##########################################################################################################

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

##########################################################################################################

def get_disc_info( path ):
	dvdinfo = fulldict()
	
	command = [
				"E:\\Handbrake\\HandBrakeCLI.exe",
				"-i", path,
				"--scan"
			]
	data = scan_output( command, "scan: DVD has" )
	titles = data.split( ":" )[3].strip()
	titles = titles.split( " " )[2].strip()
	fname = os.path.basename( path ).strip ()
	name = fname.split( "." )[0].strip()

	dvdinfo.name = name
	dvdinfo.titlecount = titles
	dvdinfo.path = path
	#media_info = MediaInfo.parse( dvd_file )
	#for track in media_info.tracks:
	#	pprint( track )

	return dvdinfo

##########################################################################################################

def get_dvd_info( path ):
	dvdinfo = fulldict()
	
	command = [
				"E:\\Handbrake\\HandBrakeCLI.exe",
				"-i", path,
				"--scan"
			]
	data = scan_output( command, "scan: DVD has" )
	titles = data.split( ":" )[3].strip()
	titles = titles.split( " " )[2].strip()
	name = os.path.split( os.path.split( path )[0] )[1]

	dvdinfo.name = name
	dvdinfo.titlecount = titles
	dvdinfo.path = path

	return dvdinfo

##########################################################################################################

def get_video_info( video_file ):
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

##########################################################################################################

def find_ifo_files( directory, ifo_files ):
	extensions = ( ".ifo" )
	# Recursively find all dvd directories in the given root.
	for root, subdirs, files in os.walk( directory ):
		for file in files:
			if file.lower().endswith( extensions ):
				if file == "VIDEO_TS.IFO":
					ifofile = os.path.join( directory, file )
					ifo_files.append( ifofile )
	return ifo_files

##########################################################################################################

def find_media_objects( args, directory, depth, findtype, extensions ):

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
					if args.debug:
						print( "File: %s" % filepath )
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
					if args.debug:
						print( "Subdir: %s" % dirpath )
					media_objects.append( dirpath )
					#media_objects = find_ifo_files( dirpath, media_objects )

	return media_objects

##########################################################################################################

def print_media( items, mediatype ):
	if mediatype == 'file':
		for item in items:
			videoinfo = get_video_info( item )
			print( "\tFile: %s" % item )
			print( "\t\tFormat: %s" % videoinfo.format )
			print( "\t\tDuration: %s" % videoinfo.duration )
			print( "\t\tResolution: %s x %s" % ( videoinfo.width, videoinfo.height ) )
			print( "" )

	elif mediatype == 'dir':
		for item in items:
			#print( "IFO File: \t%s" % item )
			name = os.path.split( os.path.split( item )[0] )[1]
			videoinfo = get_dvd_info( item )
			videoinfo.name = name
			#print( "Name: \t%s" % videoinfo.name )
			#print( "Titles:\t%s" % videoinfo.titlecount )

##########################################################################################################

def convert_videos( video_files, handbrake_profile ):
	# Convert each video file using HandBrakeCLI with the given profile.
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

##########################################################################################################

def find_packed_dvd( args ):
	extensions = ( ".iso" )
	findtype = ( 'file' )

	# Find DVD Files
	dvd_files = find_media_objects( args, args.directory, args.depth, findtype, extensions )
	if not dvd_files:
		print( "No dvd files found in the specified directory." )
		print( "" )
		#return
	else:
		if args.print:
			print_media( dvd_files, findtype )
			print( "" )

	return dvd_files

##########################################################################################################

def find_unpacked_dvd( args ):
	directory = "VIDEO_TS"
	findtype = ( 'dir' )

	# Find DVD Directories
	dvd_dirs = find_media_objects( args, args.directory, args.depth, findtype, directory )
	if not dvd_dirs:
		print( "\tNo dvd directories found in the specified root." )
		print( "" )
		return
	else:
		if args.print:
			print( "" )
			print_media( dvd_dirs, findtype )
			print( "" )

	return dvd_dirs

##########################################################################################################

def find_videos( args ):
	extensions = ( ".3gp", ".asf", ".avi", ".divx", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".mts", ".rm", ".ts", ".wmv" )
	findtype = ( 'file' )

	# Find Video Files
	video_files = find_media_objects( args, args.directory, args.depth, findtype, extensions )
	if not video_files:
		print( "No video files found in the specified directory." )
		print( "" )
		#return
	else:
		if args.print:
			print_media( video_files, findtype )
			print( "" )

	return video_files

##########################################################################################################

def scan_output( command, search ):
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

##########################################################################################################

def dischandler( args, profile ):
	if args.disc:
		discs = find_packed_dvd( args )
		if args.print:
			print( "Printing Disc Info" )
		for disc in discs:
			videoinfo = get_disc_info( disc )
			if args.print:
				print( "Disc:\t %s\t\tInfo: %s" % ( disc, videoinfo ) )


##########################################################################################################

def dvdhandler( args, profile ):
	if args.dvd:
		dvds = find_unpacked_dvd( args )
		if args.print:
			print( "Printing DVD Info" )

		for dvd in dvds:
			videoinfo = get_dvd_info( dvd )
			if args.print:
				# Print listings to stdout
				print( "DVD:\t %s\t\tInfo: %s" % ( dvd, videoinfo ) )

		print( "" )
		for dvd in dvds:
			dvdinfo = get_dvd_info( dvd )
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
				print( command )
				#print( f"Converting: {video_file} -> {output_file}" )
				if not os.path.isfile( newpath ):
					subprocess.run( command, check=True )
			print( "" )

	#HandBrakeCLI.exe -i D:\Videos\dvds\ProballDisc2\VIDEO_TS -o ProballDisc2-01.mp4 --preset-import-file x265-mp4-dvd-main.json -Z "(x265) Convert MP4 - DVD Main"

##########################################################################################################

def vidhandler( args, profile, profilehq ):
	if args.videos:
		video_files = find_videos( args )
		if args.print:
			print( "Printing Video Info" )
		for video in video_files:
			videoinfo = get_video_info( video )
			if args.print:
				print( "File:\t %s\t\tInfo: %s" % ( video, videoinfo ) )

##########################################################################################################

def convert_dvd( path, profile ):
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

##########################################################################################################

def main():
	### Command Line Arguments ###########################################################################
	parser = argparse.ArgumentParser( description="Batch convert video files using HandBrakeCLI." )
	parser.add_argument(		"--debug",		action = 'store_true',		default = False )
	parser.add_argument( "-d",	"--directory",	required=False,				default = '.',	help="Directory to search for video files." )
	parser.add_argument( "-n",	"--depth",		required=False,	type = int,					help="Search depth for video files" )
	parser.add_argument( "-p",	"--print",		action = 'store_true',		default = False )
	#parser.add_argument( "-P",	"--profile",	required=False,								help="HandBrakeCLI preset profile file." )
	parser.add_argument(		"--disc",		action = 'store_true',		default = False )
	parser.add_argument(		"--dvd",		action = 'store_true',		default = False )
	parser.add_argument(		"--videos",		action = 'store_true',		default = False )
	args = parser.parse_args()
	######################################################################################################

	hbprofile = fulldict()
	hbprofile.path = "E:\\Handbrake\\"
	hbprofile.file = "x265-mp4-dvd-main.json"
	hbprofile.name = "(x265) Convert MP4 - DVD Main"

	hbprofilehq = fulldict()
	hbprofilehq.path = "E:\\Handbrake\\"
	hbprofilehq.file = "x265-mp4-hq-main.json"
	hbprofilehq.name = "(x265) Convert MP4 - HQ Main"

	if not os.path.isfile( os.path.join( hbprofile.path, hbprofile.file ) ):
	   print( "Error: The specified HandBrake profile file does not exist." )
	else:
	   print( "Found Handbrake Profile: %s" % hbprofile.file )
	if not os.path.isfile( os.path.join( hbprofilehq.path, hbprofilehq.file ) ):
	   print( "Error: The specified HandBrake profile file does not exist." )
	else:
	   print( "Found Handbrake Profile: %s" % hbprofilehq.file )

	# List of dvd/video file extensions to search for
	
	print( "" )
	dischandler( args, hbprofile )
	print( "" )
	dvdhandler( args, hbprofile )
	print( "" )
	vidhandler( args, hbprofile, hbprofilehq )
	print( "" )

	#   return
	#convert_videos( video_files, args.profile )

##########################################################################################################

if __name__ == "__main__":
	main()
