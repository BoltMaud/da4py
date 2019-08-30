
class setOfVariables:
    def __init__(self):
        self.set={}
        self.iterator=0

    def add(self, name, listOfCouples):
        base=self.iterator
        def newfunction(listOfElements):
            result=base
            for i in range (0,len(listOfElements)):
                auxResult=(listOfElements[i]-listOfCouples[i][0])

                for c in range (i+1,len(listOfCouples)):
                    couple = listOfCouples[c]
                    auxResult*=(couple[1]-couple[0]-1)
                result+=auxResult
            return result
        self.set[name]=newfunction
        self.iterator = self.set[name]([ (couple[1]-1) for couple in listOfCouples ])+1

    def get(self,name,listOfElements):
        return self.set[name](listOfElements)


test=setOfVariables()

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

