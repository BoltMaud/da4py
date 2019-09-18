import darksider4py.main.variablesGenerator as vg

def test_add_1_variable():
    test=vg.VariablesGenerator()
    test.add("m",[(0,4),(0,5),(0,8)])
    print(test.getVarName(2))

    for i in range(0,4):
        for j in range(0, 5):
            for a in range(0, 8):
                print("aaaaa")
                print(test.getVarNumber("m",[i,j,a]))
                print(test.getVarName(1))
                assert test.getVarName(test.getVarNumber("m",[i,j,a])) == "m ["+str(i)+", "+str(j)+", "+str(a)+"]"


