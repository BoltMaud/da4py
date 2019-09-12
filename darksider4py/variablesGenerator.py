
class variablesGenerator:
    '''
    this class creates an integer per variable
    example : we need 5 "m" variables m1, m2, m3, m4, m5 then we will get 1 2 3 4 5
    '''
    def __init__(self):
        self.set={}
        self.iterator=0

    def add(self, name, listOfCouples):
        '''
        add a type of variables from p1 to p2
        :param name (string) : name of the var
        :param listOfCouples (int, int) : bounds of the var
        :return (void) create a key "name" with the numbers of the vars

        for example :
        test=variablesGenerator()
        test.add("m",[(0,4),(0,5),(0,8)])
        we have 4*5*8 m variables
        '''
        base=self.iterator
        def newfunction(listOfElements):
            '''
            a subfunction per variable that computes an element
            :param listOfElements (indexes) : in the previous example it could be [2,3,4]
            :return the value of those indexes (int)
            '''
            result=base
            #for each index
            for i in range (0,len(listOfElements)):
                # we get the initialisation of this index
                auxResult=(listOfElements[i]-listOfCouples[i][0])
                #for next index
                for c in range (i+1,len(listOfCouples)):
                    # we get the couple
                    couple = listOfCouples[c]
                    auxResult*=(couple[1]-couple[0]-1)+1
                result+=auxResult
            return result
        self.set[name]=newfunction
        self.iterator = self.set[name]([ (couple[1]-1) for couple in listOfCouples ])+1

    def getVarNumber(self,name,listOfElements):
        return self.set[name](listOfElements)

    def get(self, name):
        return self.set[name]

'''
test=variablesGenerator()

test.add("m",[(0,4),(0,5),(0,8)])
test.add("l",[(0,3),(1,5),(0,9)])
test.add("x",[(1,5)])

for i in range(0,4):
    for j in range(0, 5):
        for a in range(0, 8):
            print([i,j,a])
            print(test.get("m",[i,j,a]))

for i in range(0,3):
    for j in range(1, 5):
        for a in range(0, 9):
            print(test.get("l",[i,j,a]))

for l in range (1,5):
    print (test.get("x",[l]))
print(test.iterator)

'''