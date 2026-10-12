"""Static checks only. Run xcodebuild for Swift typechecking and simulator tests."""
from pathlib import Path
import json
import plistlib
import xml.etree.ElementTree as ET
from tree_sitter import Language, Parser
import tree_sitter_swift
from openstep_parser import OpenStepDecoder

root = Path(__file__).resolve().parents[1]
ios = root/'ios'
parser = Parser(Language(tree_sitter_swift.language()))
errors=[]
for path in ios.rglob('*.swift'):
    data=path.read_bytes()
    tree=parser.parse(data)
    if tree.root_node.has_error:
        stack=[tree.root_node]
        while stack:
            node=stack.pop()
            if node.type=='ERROR' or node.is_missing:
                errors.append(f'{path.relative_to(root)}:{node.start_point[0]+1}: {data[node.start_byte:node.end_byte][:100]!r}')
            stack.extend(node.children)
assert not errors, '\n'.join(errors)
project=OpenStepDecoder.ParseFromString((ios/'MiniKitchen.xcodeproj/project.pbxproj').read_text())
objects=project['objects']
for obj in objects.values():
    if obj['isa']=='PBXFileReference' and obj.get('sourceTree')=='<group>':
        assert (ios/obj['path']).exists(), obj['path']
    if obj['isa']=='PBXBuildFile': assert obj['fileRef'] in objects
ET.parse(ios/'MiniKitchen.xcodeproj/xcshareddata/xcschemes/MiniKitchen.xcscheme')
with (ios/'MiniKitchen/Info.plist').open('rb') as f: plistlib.load(f)
recipes=json.loads((ios/'MiniKitchen/Resources/recipes.json').read_text())
assert len(recipes)==18 and len({r['id'] for r in recipes})==18
for recipe in recipes:
    assert (ios/'MiniKitchen/Resources'/recipe['cover']).is_file()
    for step in recipe['illustrated_steps']: assert (ios/'MiniKitchen/Resources'/step['image']).is_file()
for path in (ios/'MiniKitchen').rglob('*.swift'):
    assert not any(term in path.read_text() for term in ['演示', '同步设计', '界面原型', 'AI 解析服务尚未接入', 'iPhone 与 iPad'])
print('PASS: Swift syntax, Xcode project references, scheme/plist, 18 bundled recipes and all images, production UI copy')
