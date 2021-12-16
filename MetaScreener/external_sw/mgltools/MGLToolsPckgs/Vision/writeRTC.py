from Vision.WarpIVNodes import WarpIVNode

net = Vision.ed.currentNetwork

## get node execution order
allNodes = net.getAllNodes(net.rootNodes)

nodeDef = []
dataDef = []
for nnum, node in enumerate(allNodes):
    a,b = node.getRtcSource(nnum, indent="    ")
    nodeDef.extend(a)
    dataDef.extend(b)

f = open('TestGraph0.rtc' ,'w')
f.write("include ../../InputFiles/WpGraphDataTypes.rtc\n")
f.write("include ../../InputFiles/WpGraphObjectTypes.rtc\n\n")

f.write("class Parameters {\n")
f.write("  logical PrintConstruction T\n")
f.write("  logical PrintComputations F\n")
f.write("  logical TraceComputations T\n")
f.write("}\n\n")

f.write("class Objects {\n\n")

for line in nodeDef:
    f.write(line)

f.write("}\n")

f.write("\nclass Data {\n\n")
for line in dataDef:
    f.write(line)

f.write("\n}\n")
f.close()
