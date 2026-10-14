"""Generate the checked-in, dependency-free Xcode project deterministically."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1] / 'ios'
objects={}
def uid(name): return hashlib.sha256(name.encode()).hexdigest()[:24].upper()
def ref(name): return uid(name)
def add(key, isa, **fields):
    objects[uid(key)]={'isa':isa,**fields}
    return uid(key)
def quote(v):
    if isinstance(v,list): return '(' + ', '.join(quote(x) for x in v) + ',)' if v else '()'
    if isinstance(v,dict): return '{ ' + ' '.join(f'{quote(k)} = {quote(val)};' for k,val in v.items()) + ' }'
    return json.dumps(str(v),ensure_ascii=False)

app_sources=sorted((ROOT/'MiniKitchen').rglob('*.swift'))
test_sources=sorted((ROOT/'MiniKitchenTests').glob('*.swift'))
ui_sources=sorted((ROOT/'MiniKitchenUITests').glob('*.swift'))
resources=sorted((ROOT/'MiniKitchen/Resources').glob('*')) + [ROOT/'MiniKitchen/Assets.xcassets', ROOT/'MiniKitchen/PrivacyInfo.xcprivacy']
children=[]
def files(paths, kind):
    builds=[]
    for path in paths:
        relative=str(path.relative_to(ROOT)); name='file:'+relative
        typ={'.swift':'sourcecode.swift', '.json':'text.json', '.xcassets':'folder.assetcatalog', '.xcprivacy':'text.xml'}.get(path.suffix, 'image.jpeg')
        f=add(name,'PBXFileReference',lastKnownFileType=typ,path=relative,sourceTree='<group>')
        children.append(f)
        builds.append(add('build:'+relative,'PBXBuildFile',fileRef=f))
    return builds
appfiles=files(app_sources,'source');testfiles=files(test_sources,'source');uifiles=files(ui_sources,'source');resourcefiles=files(resources,'resource')
config=add('config','PBXFileReference',lastKnownFileType='text.xcconfig',path='Config/App.xcconfig',sourceTree='<group>');children.append(config)
product=add('product','PBXFileReference',explicitFileType='wrapper.application',path='MiniKitchen.app',sourceTree='BUILT_PRODUCTS_DIR')
testproduct=add('testproduct','PBXFileReference',explicitFileType='wrapper.cfbundle',path='MiniKitchenTests.xctest',sourceTree='BUILT_PRODUCTS_DIR')
uiproduct=add('uiproduct','PBXFileReference',explicitFileType='wrapper.cfbundle',path='MiniKitchenUITests.xctest',sourceTree='BUILT_PRODUCTS_DIR')
products=add('products','PBXGroup',children=[product,testproduct,uiproduct],name='Products',sourceTree='<group>')
add('main','PBXGroup',children=children+[products],sourceTree='<group>')
for target,sources,res in [('app',appfiles,resourcefiles),('tests',testfiles,[]),('uitests',uifiles,[])]:
    add(target+'sources','PBXSourcesBuildPhase',buildActionMask='2147483647',files=sources,runOnlyForDeploymentPostprocessing='0')
    add(target+'resources','PBXResourcesBuildPhase',buildActionMask='2147483647',files=res,runOnlyForDeploymentPostprocessing='0')
    add(target+'frameworks','PBXFrameworksBuildPhase',buildActionMask='2147483647',files=[],runOnlyForDeploymentPostprocessing='0')
add('proxy','PBXContainerItemProxy',containerPortal=ref('project'),proxyType='1',remoteGlobalIDString=ref('app'),remoteInfo='MiniKitchen')
add('dependency','PBXTargetDependency',target=ref('app'),targetProxy=ref('proxy'))
for target,prod,name in [('app',product,'MiniKitchen'),('tests',testproduct,'MiniKitchenTests'),('uitests',uiproduct,'MiniKitchenUITests')]:
    add(target,'PBXNativeTarget',buildConfigurationList=ref(target+'configs'),buildPhases=[ref(target+k) for k in ['sources','frameworks','resources']],buildRules=[],dependencies=[ref('dependency')] if target!='app' else [],name=name,productName=name,productReference=prod,productType='com.apple.product-type.application' if target=='app' else ('com.apple.product-type.bundle.ui-testing' if target=='uitests' else 'com.apple.product-type.bundle.unit-test'))
for scope in ['project','app','tests','uitests']:
    configs=[]
    for mode in ['Debug','Release']:
        settings={}
        if scope=='project':
            settings={'IPHONEOS_DEPLOYMENT_TARGET':'17.0','SDKROOT':'iphoneos','SWIFT_VERSION':'5.0','CLANG_ENABLE_MODULES':'YES','SWIFT_OPTIMIZATION_LEVEL':'-Onone' if mode=='Debug' else '-O','DEBUG_INFORMATION_FORMAT':'dwarf' if mode=='Debug' else 'dwarf-with-dsym','ENABLE_TESTABILITY':'YES' if mode=='Debug' else 'NO','SWIFT_ACTIVE_COMPILATION_CONDITIONS':'DEBUG' if mode=='Debug' else ''}
        else:
            settings={'PRODUCT_NAME':'$(TARGET_NAME)','PRODUCT_BUNDLE_IDENTIFIER':'com.minikitchen.app' + ('.'+scope if scope!='app' else ''),'TARGETED_DEVICE_FAMILY':'1,2','CODE_SIGN_STYLE':'Automatic','DEVELOPMENT_TEAM':'YGQ59J98DJ','SUPPORTED_PLATFORMS':'iphoneos iphonesimulator','SWIFT_EMIT_LOC_STRINGS':'YES','LD_RUNPATH_SEARCH_PATHS':'$(inherited) @executable_path/Frameworks','GENERATE_INFOPLIST_FILE':'YES' if scope!='app' else 'NO'}
            if scope=='app': settings.update(INFOPLIST_FILE='MiniKitchen/Info.plist', CODE_SIGN_ENTITLEMENTS='MiniKitchen/MiniKitchen.entitlements', ASSETCATALOG_COMPILER_APPICON_NAME='AppIcon', MARKETING_VERSION='1.0', CURRENT_PROJECT_VERSION='4')
            elif scope=='uitests': settings.update(TEST_TARGET_NAME='MiniKitchen')
            else: settings.update(TEST_HOST='$(BUILT_PRODUCTS_DIR)/MiniKitchen.app/$(BUNDLE_EXECUTABLE_FOLDER_PATH)/MiniKitchen',BUNDLE_LOADER='$(TEST_HOST)')
        args={'buildSettings':settings,'name':mode}
        if scope=='app':args['baseConfigurationReference']=config
        configs.append(add(scope+mode,'XCBuildConfiguration',**args))
    add(scope+'configs','XCConfigurationList',buildConfigurations=configs,defaultConfigurationIsVisible='0',defaultConfigurationName='Release')
add('project','PBXProject',attributes={'LastUpgradeCheck':'1600','TargetAttributes':{ref('app'):{'CreatedOnToolsVersion':'16.0'},ref('tests'):{'CreatedOnToolsVersion':'16.0','TestTargetID':ref('app')}}},buildConfigurationList=ref('projectconfigs'),compatibilityVersion='Xcode 14.0',developmentRegion='zh-Hans',hasScannedForEncodings='0',knownRegions=['zh-Hans','en','Base'],mainGroup=ref('main'),productRefGroup=products,projectDirPath='',projectRoot='',targets=[ref('app'),ref('tests'),ref('uitests')])
project=ROOT/'MiniKitchen.xcodeproj';project.mkdir(exist_ok=True)
(project/'project.pbxproj').write_text('// !$*UTF8*$!\n'+quote({'archiveVersion':'1','classes':{},'objectVersion':'56','objects':objects,'rootObject':ref('project')})+'\n')
schemes=project/'xcshareddata/xcschemes';schemes.mkdir(parents=True,exist_ok=True)
def buildref(target,name):return f'<BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{ref(target)}" BuildableName="{name}" BlueprintName="{name.split(".")[0]}" ReferencedContainer="container:MiniKitchen.xcodeproj"/>'
appref=buildref('app','MiniKitchen.app');testref=buildref('tests','MiniKitchenTests.xctest');uiref=buildref('uitests','MiniKitchenUITests.xctest')
(schemes/'MiniKitchen.xcscheme').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="1600" version="1.3">
<BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES">{appref}</BuildActionEntry><BuildActionEntry buildForTesting="YES" buildForRunning="NO" buildForProfiling="NO" buildForArchiving="NO" buildForAnalyzing="NO">{testref}</BuildActionEntry><BuildActionEntry buildForTesting="YES" buildForRunning="NO" buildForProfiling="NO" buildForArchiving="NO" buildForAnalyzing="NO">{uiref}</BuildActionEntry></BuildActionEntries></BuildAction>
<TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES"><Testables><TestableReference skipped="NO">{testref}</TestableReference><TestableReference skipped="NO">{uiref}</TestableReference></Testables></TestAction>
<LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" debugServiceExtension="internal" allowLocationSimulation="YES"><BuildableProductRunnable runnableDebuggingMode="0">{appref}</BuildableProductRunnable></LaunchAction>
<ProfileAction buildConfiguration="Release" shouldUseLaunchSchemeArgsEnv="YES" useCustomWorkingDirectory="NO" debugDocumentVersioning="YES"><BuildableProductRunnable runnableDebuggingMode="0">{appref}</BuildableProductRunnable></ProfileAction>
<AnalyzeAction buildConfiguration="Debug"/><ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES"/>
</Scheme>''')
print(f'Generated project: {len(app_sources)} app files, {len(test_sources)} test files, {len(resources)} resources')
