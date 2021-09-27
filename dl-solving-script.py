#!/usr/bin/env python
# coding: utf-8

# ## Script for prioritized MAPF
# 
# ---
# 

# In[5]:


import subprocess
import sys
import re
import numpy as np

import time
start_time = time.time()




# These are the modules that are needed in order to succesfully execute the code below. **```subprocess```** is used in order to make the systemcalls that execute the solver and other management calls like *rm* and *cp*. **```re```** is a very important module that lets us search through the ```.lp```-files to determine robots and destination with the use of regular expressions (regex). Additionally it lets us ultimately convert the output plan into adequate input for further solving steps.
# 
# ---

# In[6]:


target = sys.argv[1]
dest   = sys.argv[2]
 
subprocess.run(["conda", "activate", "asprin"])


# When calling the python-script the given argument will be the instance we want to be solved. It throws an exception if no target has been given.
# 
# ---

# In[7]:


non_base_lines   = re.compile("init\(object\(destination.*$" )
where_robots     = re.compile("init\(object\(robot,[0-9]+\), value\(at,")
where_dests      = re.compile("init\(object\(destination,[0-9]+\), value\(at,")
find_plans       = re.compile("occurs\(object\(robot,")


# Here are the regex that are used further down to:
# * eliminate lines in the instance that are not required to model the environment. (i.e. robots, destinations, etc.)
# * find the robots initialization points (and identifiers).
# * find the destinations initialization points (and identifiers).
# * convert the plan format into an acceptable input format.
# ---

# In[8]:


robot_idents     = []       # will save the identifiers for the robots
robot_inits      = []       # will save the initialization points for the robots

dest_idents      = []       # will save the identifiers for the destinations
dest_inits       = []       # will save the initialization points for the destinations

priority_scores  = []       # will save the priority scores that determine the ordering of the solving process.


# Theese arrays will hold the lines that save the robots identifiers, ... (duh!). These are the ones that determine the order/priority with which the instance is solved.
# 
# ---

# In[9]:


target_instance  = open(target)       # this will be target | target_instance  = open(target) should work                       
temp_instance    = open("temp_instance.lp", "w+")       # a new file "temp_instance.lp" will be created


# The ```temp_instance``` will iterate through the number of robots (and destinations) and will gather the respective plans as new inputs. Before the iteration of solving, this instance will represent a base instance that only describes the environment.
# 
# ---

# In[150]:


for line in target_instance.readlines():
    
    #begin# find robot identifiers and initial starting points #######
                                                                    ##
    for match in re.finditer(where_robots, line):                   ##
        robot_inits.append(line)                                    ##
        robot_idents.append(re.findall('\d+', line)[0])         ##
                                                                    ##
    ##end## find robot identifiers and initial starting points #######
    
    #begin# find destination identifiers and initial position #######
                                                                   ##
    for match in re.finditer(where_dests, line):                   ##
        dest_inits.append(line)                                    ##
        dest_idents.append(re.findall('\d+', line)[0])         ##
                                                                   ##    
    ##end## find destination identifiers and initial position #######
    
    #begin# build base instance (without robot or destination declarations) #######
                                                                                 ##    
    line = re.sub(non_base_lines, "", line)                                      ##
    temp_instance.write(line)                                                    ##
                                                                                 ##
    ##end## build base instance (without robot or destination declarations) #######

target_instance.close()
temp_instance.close()

'''
print(robot_idents)
print(robot_inits)
print(dest_idents)
print(dest_inits)
'''


# This section uses some regex described above to find the robots and destinations identifiers and initial positions. In the end we delete all non-essential lines for describing the environment.
# 
# ---

# In[151]:


for i in range(len(robot_idents)):
    x1 = int(re.findall('\d+', robot_inits[i])[1])
    y1 = int(re.findall('\d+', robot_inits[i])[2])
    
    x2 = int(re.findall('\d+', dest_inits[i])[1])
    y2 = int(re.findall('\d+', dest_inits[i])[2])
     
    manhattan = np.abs(x1-x2) + np.abs(y1-y2)
    
    priority_scores.append(manhattan)


priority_scores, robot_idents, dest_idents, dest_inits = (list(t) for t in zip(*sorted(zip(priority_scores, robot_idents, dest_idents, dest_inits), reverse=True)))


print(priority_scores)
print(robot_idents)
'''
print(dest_idents)
print(dest_inits)
'''


# 

# In[152]:


def solve_for_robot_i(i):
    
    #begin# extending temp_instance.lp by destination declaration for robot i ########        
                                                                                    ##
    index = robot_idents.index(i)                                                   ##
    temp_instance = open("temp_instance.lp", "a")                                   ##
    temp_instance.write(dest_inits[index])  # write destination initialization      ##
    temp_instance.close()                                                           ##
                                                                                    ##
    ##end## extending temp_instance.lp by destination declaration for robot i ########           
    
    ####### solve for robot i and its respective destination. Save the output in temp_plan.lp   
    subprocess.run("clingo ./testsolver.lp temp_instance.lp > temp_plan.lp --outf=1 --out-atomf='%s.' --out-ifs='\n' --time-limit=10", shell=True)    
    
    temp_instance = open("temp_instance.lp", "r")       # alter this instance to contain a converted plan for further solving
    lines = temp_instance.readlines()
    temp_instance.close()
    
    temp_instance = open("temp_instance.lp", "w")
    for line in lines:
        if line.strip("\n") != dest_inits[index][:-1]:
            temp_instance.write(line)
    
    #begin# extending temp_instance.lp by the plan for robot i
    
    # occurs(object(robot,1),action(move,(0,-1)),2)
    # position(     robot(R),            (X, Y) ,T)
    
    plan_instance = open("temp_plan.lp", "r+")          # read from plan-instance
    
    for line in plan_instance.readlines():
        for match in re.finditer(find_plans, line):
            temp_instance.write(line)        
            
    plan_instance.close()        
    temp_instance.close()


# **This is the heart-piece of the script.**
# 
# This section is divided into three parts that allow for an iterative solving process.
# ### Part I
# simply extends the current iteration of the instance by the robot and destination locations and identifiers that have been extracted previously.
# 
# ### Part II
# is the execution of the embedded solver. Note that this solver only solves for one robot at the time! Therefore this solver could be replaced by any optimal single agent solver. The plan is saved in a file ```temp_plan.lp```
# 
# ### Part III
# extends the temporary instance by the ```occurs```-statements that are used within the dl-solver.

# In[153]:


for identifier in robot_idents:
    solve_for_robot_i(identifier)


# This iterates through the array of robot identifiers and solves the instance with their respective destination.
# 
# ---

# In[40]:


subprocess.run(["rm", "temp_instance.lp"])
subprocess.run(["cp", "temp_plan.lp", dest])
subprocess.run(["rm", "temp_plan.lp"])

# This deletes the files that are no longer needed. ```target_plan.lp``` can later be replaced by a given argument when calling the script.
# 
# ---

print("--- %s seconds ---" % (time.time() - start_time))




