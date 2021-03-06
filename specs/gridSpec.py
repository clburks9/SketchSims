import sys
sys.path.append("../src")
from softmaxModels import Softmax
import numpy as np
from copy import deepcopy
import matplotlib.pyplot as plt
import math
from shapely.geometry import Polygon, Point
from sketchGen import Sketch

numActs = 4
gamma = .9
maxTime = .2
maxDepth = 10
c = .2
drone_falseNeg = .001
drone_falsePos = .001
human_availability = 0.9; 
human_accuracy = 0.95; 
human_class_thresh = 0.8; #has to be at least x% of the maximum 
detect_length = 150; 
capture_length = 75;


maxTreeQueries = 1000
sampleCount = 1000
agentSpeed = 30 #m/s
problemName = 'Grid'



def generate_s(s, a):

    speed = 15 #m/s, about 35 mph
    offRoadSpeed = 5 #m/s, about 9 mph
    dev = 5
    offRoadDev = 1
    leaveRoadChance = 1/60 #About every minute or so

    #sprime = deepcopy(s);
    sprime = [s[0],s[1],s[2],s[3],s[4],s[5],s[6]]

    c = sprime[4].loc
    g = sprime[5].loc
    mode = sprime[6]

    # if mode is 0, check for mode transition
    if(sprime[6] == 0):
        coin = np.random.random()
        if(coin < leaveRoadChance):
            sprime[6] = 1

            # if mode transitions to 1, pick random new goal
            # but only pick from neighbors neighbors, so that you can't easily cross multiple roads
            l = [i for i in range(0, len(sprime[5].neighbors))]
            if(len(l) > 1):
                l.remove(sprime[5].neighbors.index(sprime[4]))
                for l1 in l:
                    if(sprime[5].neighbors[l1].loc[0] == sprime[5].loc[0] and sprime[5].loc[0] == sprime[4].loc[0]):
                        l.remove(l1); 
                    elif(sprime[5].neighbors[l1].loc[1] == sprime[5].loc[1] and sprime[5].loc[1] == sprime[4].loc[1]):
                        l.remove(l1); 
            newGoal = sprime[5].neighbors[np.random.choice(l)]; 
            g = newGoal.loc
            sprime[5] = newGoal

    if(sprime[6] == 0):
        # move it one step along the distance between cur and goal
        if(c[0] > g[0]):
            sprime[2] -= speed + np.random.normal(0, dev)
        elif(c[0] < g[0]):
            sprime[2] += speed + np.random.normal(0, dev)

        if(c[1] > g[1]):
            sprime[3] -= speed + np.random.normal(0, dev)
        elif(c[1] < g[1]):
            sprime[3] += speed + np.random.normal(0, dev)
    elif(sprime[6] == 1):

        #find vector from current position to goal
        vec = [g[0]-sprime[2],g[1]-sprime[3]]; 
        norm = np.sqrt(vec[0]*vec[0] + vec[1]*vec[1]); 
        vec[0] *= (offRoadSpeed+np.random.normal(0,offRoadDev))/norm 
        vec[1] *= (offRoadSpeed+np.random.normal(0,offRoadDev))/norm 

        sprime[2] += vec[0]; 
        sprime[3] += vec[1]; 



    # if point has reached goal choose new goal
    # note: You'll want to make this not perfect equivalence
    if(distance([sprime[2], sprime[3]], c) > distance(c, g)):
        #print("Goal Reached!!!");
        l = [i for i in range(0, len(sprime[5].neighbors))]
        if(len(l) > 1):
            if(sprime[6] == 0):
                l.remove(sprime[5].neighbors.index(sprime[4]))
        sprime[4] = sprime[5]
        sprime[2] = sprime[4].loc[0]
        sprime[3] = sprime[4].loc[1]
        tmp = np.random.choice(l)
        sprime[5] = sprime[4].neighbors[tmp]
        sprime[6] = 0

    # actions
    # 0: left
    # 1: right
    # 2: up
    # 3: down

    # Move the Agent
    if(a[0] == 0):
        sprime[0] -= agentSpeed
    elif(a[0] == 1):
        sprime[0] += agentSpeed
    elif(a[0] == 2):
        sprime[1] += agentSpeed
    elif(a[0] == 3):
        sprime[1] -= agentSpeed
    elif(a[0] == 4):
        #northwest
        sprime[0] -= agentSpeed; 
        sprime[1] += agentSpeed; 
    elif(a[0] == 5):
        #northeast
        sprime[0] += agentSpeed; 
        sprime[1] += agentSpeed; 
    elif(a[0] == 6):
        #southeast
        sprime[0] += agentSpeed; 
        sprime[1] -= agentSpeed; 
    elif(a[0] == 7):
        #southwest
        sprime[0] -= agentSpeed; 
        sprime[1] -= agentSpeed; 


    sprime[0] = min(1000, max(0, sprime[0]))
    sprime[1] = min(1000, max(0, sprime[1]))

    return sprime



def dist(s):
    return np.sqrt((s[0]-s[2])**2 + (s[1]-s[3])**2)


def distance(a, b):
    return np.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


def generate_r(s, a):

    #return max(100-dist(s),0); 
    #return 1/dist(s)
    if(a[0] is not None):
        theta_options = [180,0,90,270,135,45,315,225]
        theta = theta_options[a[0]]; 
    else:
        theta = 90; 

    capture_points = [[s[0], s[1]], [s[0]+capture_length*math.cos(2*-0.261799+math.radians(theta)), s[1]+capture_length*math.sin(2*-0.261799+math.radians(
        theta))], [s[0]+capture_length*math.cos(2*0.261799+math.radians(theta)), s[1]+capture_length*math.sin(2*0.261799+math.radians(theta))]]
    capture_poly = Polygon(capture_points); 

    target = Point(s[2],s[3]); 

    if(capture_poly.contains(target)):
        return 100; 
    elif(a[1][0] is None):
        #return 100-100*(dist(s)/1000); 
        #return min(1000,1000/dist(s));
        #return 1; 
        return -1; 
    else:
        return -4; 
        
    #return 100 - 100*(dist(s)/1000); 


def generate_o(s, a):


    #Observations have two parts
    #----------------------------------------------------------
    #1. Drone view: Captured/Detect/Null
    #2. Human Query Response: Yes/No/Null


    #First: Check if Drone can see target in view
    #----------------------------------------------------------
    #90 degree angle
    #Can see targets at 50, captured at 25
    drone_response = "Null";

    if(a[0] is not None):
        theta_options = [180,0,90,270,135,45,315,225]
        theta = theta_options[a[0]]; 
    else:
        theta = 90; 

    #Check to see if the drone view failed, false negative
    flip = np.random.random(); 
    if(flip > drone_falseNeg):

        detect_points = [[s[0], s[1]], [s[0]+detect_length*math.cos(2*-0.261799+math.radians(theta)), s[1]+detect_length*math.sin(2*-0.261799+math.radians(
            theta))], [s[0]+detect_length*math.cos(2*0.261799+math.radians(theta)), s[1]+detect_length*math.sin(2*0.261799+math.radians(theta))]]
        detect_poly = Polygon(detect_points); 


        capture_points = [[s[0], s[1]], [s[0]+capture_length*math.cos(2*-0.261799+math.radians(theta)), s[1]+capture_length*math.sin(2*-0.261799+math.radians(
            theta))], [s[0]+capture_length*math.cos(2*0.261799+math.radians(theta)), s[1]+capture_length*math.sin(2*0.261799+math.radians(theta))]]
        capture_poly = Polygon(capture_points); 

        target = Point(s[2],s[3]); 

        if(detect_poly.contains(target)):
            drone_response = "Detect"
            if(capture_poly.contains(target)):
                drone_response = "Captured"

    #False Positive
    flip = np.random.random();
    if(flip < drone_falsePos):
        drone_response = "Detect"



    #Second: See what the human said
    #----------------------------------------------------------
    #Action structure: [move, [ske,dir]]
    #4 moves, N sketches, 17 dirs
    #actual sketches and directions
    
    human_response = "Null"
    flip = np.random.random(); 
    if(flip < human_availability):
        if(a[1][0] is not None):
            ske = a[1][0]; 
            # ske = sketchSet[a[1][0]]; 
            human_response = ske.answerQuestion([s[2],s[3]],a[1][1],thresh=human_class_thresh); 





    full_repsonse = drone_response + " " + human_response; 

    return full_repsonse;


def estimate_value(s, h):
    # how far can you get in the depth left


    #return min(100,1/dist(s))

    #return min(1000,1000/dist(s));
    return 100-dist(s)/agentSpeed;


def rollout(s, depth):

    if(depth <= 0):
        return 0
    else:
        # random action
        a = np.random.randint(0, 8)
        sprime = generate_s(s, [a])
        r = generate_r(s, [a])
        return r + gamma*rollout(sprime, depth-1)


def isTerminal(s, act):

    if(act[0] is not None):
        theta_options = [180,0,90,270,135,45,315,225]
        theta = theta_options[act[0]]; 
    else:
        theta = 90; 


    capture_points = [[s[0], s[1]], [s[0]+capture_length*math.cos(2*-0.261799+math.radians(theta)), s[1]+capture_length*math.sin(2*-0.261799+math.radians(
        theta))], [s[0]+capture_length*math.cos(2*0.261799+math.radians(theta)), s[1]+capture_length*math.sin(2*0.261799+math.radians(theta))]]
    capture_poly = Polygon(capture_points); 

    target = Point(s[2],s[3]); 

    if(capture_poly.contains(target)):
        return True; 
    else:
        return False; 




def demoAnsweringHuman():
    params = {'centroid': [500, 500], 'dist_nom': 50, 'dist_noise': .25,
          'angle_noise': .3, 'pois_mean': 4, 'area_multiplier': 5, 'name': "Test", 'steepness': 20}
    ske = Sketch(params,seed=3)

    #colors = {'Null Null': 'red', 'Detect Null': 'blue', 'Captured Null': 'green'}


    allColors = []; 
    allScattersX = []; 
    allScattersY = []; 
    #label = 'Near NorthWest'
    #label = 'NorthEast'
    label = 'North'
    # label = 'Near'

    for i in range(0, 40):
        for j in range(0,40):

            s = [500, 500, 300+i*10, 300+j*10]
            o = generate_o(s, [None,[ske,label]])
            #plt.scatter(s[2], s[3], c=colors[o])
            allScattersX.append(s[2]); 
            allScattersY.append(s[3]); 
            if("Yes" in o):
                allColors.append('green'); 
            elif("No" in o):
                allColors.append('red');
            else:
                allColors.append('black'); 

    plt.scatter(allScattersX,allScattersY,color=allColors)
    plt.scatter(ske.points[:,0],ske.points[:,1],color='blue',s=100); 

    plt.ylim([0, 1000])
    plt.xlim([0, 1000])
    plt.show()



if __name__ == '__main__':

    demoAnsweringHuman(); 