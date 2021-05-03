import xml.etree.ElementTree as ET
import pathlib
import json

#
# more on https://www.w3schools.com/xml/xpath_syntax.asp
#

basedir = pathlib.Path().absolute()
tree = ET.parse(str(basedir)+'/src/data.xml')
root = tree.getroot()
print(str(root))

for child in root:
 print(child.tag, child.attrib)

print(root[0][1].text) 

for country in root.findall('country'):
     rank = country.find('rank').text
     name = country.get('name')
     print(name, rank)

print(str(root.findall(".//*[@name='Singapore']/year")))  

print("final json data:")
json_data = { 
    "contries: ": [
        str(x.get("name")) for x in root.findall("./country/") if str(x.get("name")) != "None"
    ]
}
print(json.dumps(json_data, indent=2, sort_keys=True))