import os, shutil, subprocess, sys
from . import hashCheck

BRO_ARCHIVE = 'bro-2.5.1.tar.gz'
BRO_DOWNLOAD_URLS = [
	'https://www.bro.org/downloads/bro-2.5.1.tar.gz',
	'https://download.zeek.org/bro-2.5.1.tar.gz',
	'https://github.com/zeek/zeek/releases/download/v2.5.1/bro-2.5.1.tar.gz'
]

def download_bro_archive():
	for url in BRO_DOWNLOAD_URLS:
		print("  Trying %s" % url)
		if os.path.isfile(BRO_ARCHIVE):
			os.remove(BRO_ARCHIVE)
		result = subprocess.run(['sudo', 'wget', '-O', BRO_ARCHIVE, url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		if result.returncode == 0 and os.path.isfile(BRO_ARCHIVE) and os.path.getsize(BRO_ARCHIVE) > 0:
			return True
	return False

def install(chosenInterface,webServer):
	
	broLatest='2.5.1'
	
	cwd=os.getcwd()
	
	broInstalled=False
	if os.path.isfile('/opt/nsm/bro/bin/bro'):
		broVersion=os.popen('sudo /opt/nsm/bro/bin/bro -version  2>&1').read()
		if broLatest == broVersion.split()[2]:
			broInstalled=True
	if broInstalled==False:
		print("Installing Bro IDS")
		print("  Downloading Bro IDS 2.5.1")
		if not download_bro_archive():
			sys.exit('Error downloading Bro. All known URLs failed: %s' % ', '.join(BRO_DOWNLOAD_URLS))
		if not hashCheck.checkHash(BRO_ARCHIVE):
			sys.exit('Error downloading Bro, mismatched file hashes')
		print("  Unpacking Bro Code")
		os.popen('sudo tar -xzf bro-2.5.1.tar.gz').read()
		print("  Creating Bro Directory Structures")
		if not os.path.exists('/opt/nsm'):
			os.makedirs('/opt/nsm')
		if not os.path.exists('/opt/nsm/bro'):
			os.makedirs('/opt/nsm/bro')
		os.chdir('bro-2.5.1')
		print("  Configuring Bro Code")
		os.popen('sudo ./configure --prefix=/opt/nsm/bro 2>&1').read()
		print("  Making Bro Code")
		os.popen('sudo make 2>&1').read()
		print("  Installing Bro Code")
		os.popen('sudo make install 2>&1').read()
		print("  Cleaning Up Bro Installation Files")
		os.chdir(cwd)
		os.remove(BRO_ARCHIVE)
		shutil.rmtree("bro-2.5.1/")
		
		#Update node.cfg to listen on chosen interface
		print("  Configuring Bro")
		newInterfaceString='interface=%s\n' % chosenInterface
		nodeCfgPath = '/opt/nsm/bro/etc/node.cfg'
		nodeOrigPath = '/opt/nsm/bro/etc/node.orig'
		if os.path.isfile(nodeCfgPath):
			shutil.move(nodeCfgPath, nodeOrigPath)
			with open(nodeOrigPath, "rt") as fileIn:
				with open(nodeCfgPath, "wt") as fileOut:
					for line in fileIn:
						if line.rstrip() == "interface=eth0":
							line = newInterfaceString
						fileOut.write(line)
		else:
			# Some builds don't ship node.cfg; write a minimal standalone config.
			if not os.path.isdir('/opt/nsm/bro/etc'):
				os.makedirs('/opt/nsm/bro/etc')
			with open(nodeCfgPath, 'wt') as nodeFile:
				nodeFile.write('[bro]\n')
				nodeFile.write('type=standalone\n')
				nodeFile.write('host=localhost\n')
				nodeFile.write(newInterfaceString)
		#ignore communication between sensor and webServer, writes a ton of noise
		if webServer != 'localhost':
			broCtlCfgPath = "/opt/nsm/bro/etc/broctl.cfg"
			if os.path.isfile(broCtlCfgPath):
				with open(broCtlCfgPath, "a") as broCtlFile:
					broCtlFile.write("\nbroargs = -f 'not host %s'\n" % webServer)
			else:
				print("  Warning: broctl.cfg not found; skipping broargs tuning")
		
		print("  Deploying and Starting Bro")
		os.popen('sudo /opt/nsm/bro/bin/broctl deploy').read()
		os.popen('sudo /opt/nsm/bro/bin/broctl start').read()
	else:
		print("Bro already installed...")
