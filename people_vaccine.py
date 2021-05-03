import collections
import random
import math
import matplotlib.pyplot as plt
import numpy as np

import sys
import json



# quarantine and vaccine

# index --> [0,self.popsize)
# health: 0 --> healthy, 1--> infected, 2--> dead
# pos --> (x,y) 
# quarantine --> True/False
# vaccine --> True/False



class People:
    def __init__(self,index,health,pos,quarantine,vaccine,move,direction):
        self.index = index
        self.infect_date = 0
        self.health = health
        self.pos = pos
        self.quarantine = quarantine
        self.vaccine = vaccine
        self.move = move
        self.direction = direction

    def print_person(self):
        print("health", self.health)
        print("pos", self.pos)

    


class City:
    def __init__(self,mobility=0.5,quarantine_rate=0.5,daily_vaccine_rate=0.01):
        self.healthy = set()
        self.vaccinated = set()
        self.infected = set()
        self.death = set()
        # (x,y) : person
        self.graph = {}
        # self.num_iter = 0
        # (x,y) : #infected person
        self.matrix_length = 200
        self.pop_size = self.matrix_length**2//4
        self.init_infected_rate = 0.2
        self.infected_rate = 0
        self.mobility = mobility
        # 1-e^(-lam*(x+1)) - (1-e^(-lam*x)
        self.death_rate = 0.1
        self.recover_rate = 1 - self.death_rate
        self.re_list = []

        self.infected_period = 30

        self.daily_vaccine_rate = daily_vaccine_rate

        # vaccine ineffective
        self.vaccine_effective = 0.05

        # 1-e^(-lam*(x+1)) - (1-e^(-lam*x)
        self.lam_death = -1*math.log(1-self.death_rate)/ self.infected_period
        #  (1-e^(-lam)) - (1-e^(-lam*(x+1)) + (1-e^(-lam*x))
        self.lam_recover = -1*math.log(1-self.recover_rate)/ self.infected_period

        self.num_iter = 550
        self.K = 20
        self.quarantine_rate = 0.5
        # in each iteration, there will be this portion of healthy people get vaccinated
        # self.vaccine_rate = 0.001

        self.self_cure_rate = 0.001
        self.Imax = 0

        # days we need to produce vaccine
        self.vaccine_release = 200
        directions = [(i,j) for i in range(-1,2) for j in range(-1,2) if (i,j)!=(0,0)]

        random_init = random.sample([(i,j) for i in range(self.matrix_length) for j in range(self.matrix_length)], self.pop_size)
        index = 0
        for x,y in random_init:
            
            infected = random.uniform(0,1)
            quarantine = random.uniform(0,1)
            random_direction = random.choice(directions)
            person = People(index,(1 if infected<self.init_infected_rate else 0), (x,y), (True if quarantine<self.quarantine_rate else False), False, (True if random.uniform(0,1)<self.mobility else False),random_direction)
            if person.health==0:
                self.healthy.add(person)
            else:
                self.infected.add(person)
                # self.graph_infected[x,y] += 1
            self.graph[x,y] = person
            index+=1
        
        self.re_list += [len(self.infected)]
        
        # self.print_graph()

        
    def exponential(self, lam, x):
        return 1-math.exp(-1 * lam*x)


    def print_graph(self):
        print(self.graph.keys())
        mat = [[-1]*self.matrix_length for _ in range(self.matrix_length)]
        for i in range(self.matrix_length):
            for j in range(self.matrix_length):
                if (i,j) in self.graph:
                    mat[i][j] = self.graph[i,j].health
        print(mat)
        print('Death: ', len(self.death))
        print('Infected: ', len(self.infected))
        print('Vaccinated: ', len(self.vaccinated))
        

    def iter(self):
        # self.num_iter += 1
        # run iterations
        directions = [(i,j) for i in range(-1,2) for j in range(-1,2) if (i,j)!=(0,0)]
        # self.re_list += [len(self.infected)]
        for person in self.healthy|self.infected:
            if person.move: #move
                x,y = person.pos
                dx,dy = person.direction
                nx,ny = x+dx,y+dy
                if not (0<=nx<self.matrix_length and 0<=ny<self.matrix_length):
                    directions.remove((dx,dy))
                    person.direction = random.choice(directions)
                    directions.append((dx,dy))
                elif (nx,ny) in self.graph:
                    neighbor = self.graph[nx,ny]
                    if neighbor.health == 1: # neighbor infected
                        if person.health == 0:
                            if not person.vaccine or random.uniform(0, 1)< self.vaccine_effective:

                                self.healthy.remove(person)
                                self.infected.add(person)
                        person.health = 1 # infected
                    elif person.health == 1: # neighbor infected
                        if neighbor.health == 0:
                            if not person.vaccine or random.uniform(0, 1)< self.vaccine_effective:
                                self.healthy.remove(neighbor)
                                self.infected.add(neighbor)
                        neighbor.health = 1 # infected
                    directions.remove((dx,dy))
                    person.direction = random.choice(directions)
                    directions.append((dx,dy))
                    
                else:# no collision
                    # person.print_person()
                    person.pos = (nx,ny)
                    del self.graph[x,y]
                    self.graph[nx,ny] = person

                # move to new position
                
        for person in self.infected:
            person.infect_date += 1
        # go through each cell and check if someone could be infected

        for i in range(self.matrix_length):
            for j in range(self.matrix_length):
                if (i,j) not in self.graph:
                    continue
                
                person = self.graph[i,j]

                # recover
                if person.health == 1 and (person.infect_date == self.infected_period or random.uniform(0,1) < self.exponential(self.lam_recover, 0) - self.exponential(self.lam_recover, person.infect_date+1) + self.exponential(self.lam_recover, person.infect_date)):
                    person.health = 0
                    person.infect_date = 0
                    self.healthy.add(person)
                    self.infected.remove(person)
                
                if person.health == 0 and random.uniform(0, 1)<self.daily_vaccine_rate:
                    person.vaccine = True
                    
                # death
                elif person.health == 1 and (random.uniform(0,1) < self.exponential(self.lam_death, person.infect_date+1) - self.exponential(self.lam_death, person.infect_date)):
                    person.health = 2
                    self.death.add(person)
                    # print(person in self.infected, )
                    self.infected.remove(person)
                    del self.graph[i,j]
        # self.print_graph()
        # self.animation()
        self.re_list += [len(self.infected)]


    def animation(self):
        # Make a 9x9 grid...
        nrows = ncols = self.matrix_length
        image = [[-2]*nrows for i in range(nrows)]
        for i in range(self.matrix_length):
            for j in range(self.matrix_length):
                if (i,j) in self.graph:
                    image[i][j] = self.graph[i,j].health
        

        image = np.array(image).reshape((nrows, ncols))

        # row_labels = range(nrows)
        # col_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        plt.matshow(image)
        # plt.xticks(range(ncols), col_labels)
        # plt.yticks(range(nrows), row_labels)
        plt.show()

if __name__ == '__main__':
    print("main")
    Re_arr = []
    Imax_arr = []
    num_iter_arr = []
    vaccine_rate_arr = [0.01,0.02,0.3]
    
    for v in vaccine_rate_arr:
        for j in range(600):
            print(j)
            new_city = City(daily_vaccine_rate=v)
            num_iter = 550
            for i in range(num_iter):
                if len(new_city.healthy)+len(new_city.infected) == 0:
                    break
                if i and len(new_city.infected) == 0:
                    break
                # print(i)
                new_city.iter()

            Re = sum([max(y-x,0)/max(x,1) for x,y in zip(new_city.re_list,new_city.re_list[1:])])#/max(1,len(new_city.re_list)-1)
            Imax = max(new_city.re_list)
            num_iter = len(new_city.re_list)-1

            Re_arr += [Re]
            Imax_arr += [Imax]
            num_iter_arr += [num_iter]

        filepath = sys.argv[1]
        f = open(filepath,'a')
        json_obj = {
            "Re": sum(Re_arr)/len(Re_arr),
            "Imax": sum(Imax_arr)/len(Imax_arr),
            "num_iter": sum(num_iter_arr)/len(num_iter_arr),
            "vaccine_rate": v
        }
        f.write(json.dumps(json_obj)+"\n")
        print(Re)
        print(Imax)
        print(num_iter)