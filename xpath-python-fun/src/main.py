import xml.etree.ElementTree as ET
import pathlib

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

json_data = {
    x.attrib("name"): {
        "r": 42
    }
    for x in root.findall(".//year/")
}
#print(root.findall(".//country/"))
print(json_data)