import os

CADET= "/Users/mboltenhagen/Documents/PhD/2QBF/cadet/cadet"


def runCadet(filename="temp.qdimacs",outputfile="temp2.qdimacs"):
    os.system(CADET+ " --qdimacs_out "+filename+ ">"+outputfile)

def cadetOutputQDimacs(filename="temp2.qdimacs"):
    listOfVars=[]
    file = open(filename,"r")
    for l in file:
        if "c Vc" in l:
            listOfVars+=l.split("Vc")[1].split("c ")
            del listOfVars[-1]
    listOfPositives=[int(e) for e in listOfVars if "-" not in e]
    listOfNegatives=[int(e.replace("-","")) for e in listOfVars if "-" in e]
    file.close()
    return  listOfPositives,listOfNegatives


def writeQDimacs(numberOfVars,listOfForAll, listOfExist, listOfCnf,filename="temp.qdimacs"):
    print("he ou")
    file = open(filename,"w")
    file.write("p cnf "+str(numberOfVars) +" "+str(len(listOfCnf))+" 0\n")
    file.write("a")
    [file.write(" "+str(a)) for a in listOfForAll]
    file.write(" 0\ne")
    [file.write(" "+str(e)) for e in listOfExist]
    file.write(" 0\n")
    for clause in listOfCnf:
        [file.write(str(e)+" ") for e in clause]
        file.write("0\n")
    file.close()






