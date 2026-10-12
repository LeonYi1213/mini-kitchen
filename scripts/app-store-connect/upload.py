#!/usr/bin/env python3
"""Upload a checked archive using the existing local account connection."""
import json
import plistlib
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
archive = Path(sys.argv[1]).resolve()
a = json.loads((Path.home()/'.codex/memories/app-delivery-connections.json').read_text())['apple_account']
c = json.loads((ROOT/'scripts/app-store-connect/release-config.json').read_text())
assert c.get('app_id'), 'Create the App Store Connect app record and run prepare-private-beta.rb first.'
app=archive/'Products/Applications/MiniKitchen.app'
p=plistlib.loads((app/'Info.plist').read_bytes())
assert p['CFBundleIdentifier']==c['bundle_id']
assert p['CFBundleShortVersionString']==c['version'] and p['CFBundleVersion']==c['build']
assert p.get('CFBundleIcons') and (app/'PrivacyInfo.xcprivacy').exists()
assert p.get('ImportServiceURL','').startswith('https://') and p.get('ImportServiceToken'), 'Configure and verify the cloud service before upload.'
subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
subprocess.run(['xcodebuild','-exportArchive','-archivePath',str(archive),'-exportPath',str(ROOT/'.local/release/export'),'-exportOptionsPlist',str(ROOT/'scripts/app-store-connect/ExportOptions.plist'),'-allowProvisioningUpdates','-authenticationKeyPath',a['asc_private_key_path'],'-authenticationKeyID',a['asc_key_id'],'-authenticationKeyIssuerID',a['asc_issuer_id']],check=True)
