# Import dependancies.
import csv
import math
import tweepy
from loginInfo import *
import re
import os

# Authorize Twitter login
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

# Get the x latest direct messages.
dms = api.direct_messages(count=8)

# Reverse the order of the messages so they are processed as they were sent
dms = dms[::-1]

# Function to count the wins and losses of a given player. Returns an array of [wins, losses].
def countWL(name):
    wins = 0
    losses = 0
    for x in range(0, numGames):
        if name == csvMatrix[x][1]:
            if csvMatrix[x][2] > csvMatrix[x][3]:
                wins += 1
            else:
                losses += 1
        if name == csvMatrix[x][4]:
            if csvMatrix[x][3] > csvMatrix[x][2]:
                wins += 1
            else:
                losses += 1
    return([wins, losses])

# Function to calculate the win and loss percentage for a given player. Returns an array of [win %, loss %].
def percentages(name):
    try:
        rawWP = countWL(name)[0]/(countWL(name)[0]+countWL(name)[1])*100
    except ZeroDivisionError:
        rawWP = 0
    try:
        rawLP = countWL(name)[1]/(countWL(name)[0]+countWL(name)[1])*100
    except ZeroDivisionError:
        rawLP = 0
    formattedWP = format(rawWP, '.2f')
    formattedLP = format(rawLP, '.2f')
    return([formattedWP,formattedLP])

# Function to calculate the goals scored and goal conceded for a given player. Returns an array of [goals scores, goals conceded].
def goals(name):
    goalsFor = 0
    goalsAgainst = 0
    for x in range(0, numGames):
        if name == csvMatrix[x][1]:
            goalsFor += math.floor(float(csvMatrix[x][2]))
            goalsAgainst += math.floor(float(csvMatrix[x][3]))
        if name == csvMatrix[x][4]:
            goalsFor += math.floor(float(csvMatrix[x][3]))
            goalsAgainst += math.floor(float(csvMatrix[x][2]))
    return([goalsFor, goalsAgainst])

# Function to compile stats for every player into a CSV file. Redundant in Twitter-side use.
def compileStats():
    with open(locStats,'w+') as file:
        file.write('Player,Played,Wins,Losses,Win %,Goals For,Goals Against,Goal Difference')
        for player in playerList:
            file.write('\n')
            string = player+','+str(sum(countWL(player)))+','+str(countWL(player)[0])+','+str(countWL(player)[1])+','+str(
                percentages(player)[0])+','+str(goals(player)[0])+','+str(goals(player)[1])+','+str(goals(player)[0]-goals(
                    player)[1])
            file.write(string)
    file.close()

# Function to check the type of functionality required from a given message.
def checkValidity(string):
    if (string == '!HELP') or (string == '!DELETE') or (string == '!RESET12345'):
        return(string[1:])
    if string.count(',') == 3:
        try:
            float(((dm.text).split(sep=',', maxsplit=4)[1]).replace(' ',''))
            float(((dm.text).split(sep=',', maxsplit=4)[2]).replace(' ',''))
            return('true')
        except ValueError:
            return('false')
    if string[:7] == '!STATS ':
        return('stats'+string.replace(string[:7], ''))
    else:
        return('false')

# Function to update the CSV file with the scores stored in the array.
def updateCSV(csvMatrix):
    with open(locScores, 'w') as f:
        writer = csv.writer(f, delimiter=',', lineterminator = '\n')
        for x in range(numGames):
            if csvMatrix:
                writer.writerow(csvMatrix[x])

# Function to generate a list of every player who has had a score entered.
def genPlayerList():
    for x in range(0,numGames):
        if csvMatrix:
            if csvMatrix[x][1] not in playerList:
                playerList.append(csvMatrix[x][1])
            if csvMatrix[x][4] not in playerList:
                playerList.append(csvMatrix[x][4])

# Function to read in the list of all DMs already processed.
def readinIDs():
    file = open(locDMIDs, 'r')
    for line in file:
        readIDs.append(str(line).replace('\n',''))

#Function to write the text file the list of all DMs already processed.
def writeinIDs():
    file = open(locDMIDs, 'w')
    for readID in readIDs:
        file.write(readID+'\n')
    
# Initialise lists and variables.
csvMatrix = []
numGames = 0
playerList = []
dmIDs = []
readIDs = []
locScores = '/home/pi/FIFAScoresBot/scores.csv'
locStats = '/home/pi/FIFAScoresBot/stats.csv'
locDMIDs = '/home/pi/FIFAScoresBot/procIDs.txt'

# Read all of the scores stored in the CSV into the csvMatrix list.
with open(locScores, newline='') as csvfile:
    scoreReader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in scoreReader:
        numGames += 1
        csvMatrix.append(row)

readinIDs()

if numGames != 0:
    genPlayerList()
    for x in range(numGames):
        dmIDs.append(csvMatrix[x][0])

# Go through every DM that has not already been processed and provide the required functionality.
# This could probably be made cleaner with various other procedures: it's a bit of a mess.
for dm in dms:
    validityType = checkValidity((dm.text).upper())
    if str(dm.id) not in readIDs:
        readIDs.append(str(dm.id))
        if validityType == 'true':
            readIDs.append(str(dm.id))
            lineToAppend = [str(dm.id)]
            for x in range(0,4):
                lineToAppend.append(((dm.text).split(sep=',', maxsplit=4)[x]).replace(' ','').upper())
            csvMatrix.append(lineToAppend)
            api.send_direct_message(dm.sender_id, text="Thank you. Your score has been sucessfully recorded.")
            numGames += 1
            genPlayerList()
            updateCSV(csvMatrix)
        if validityType == 'HELP':
            api.send_direct_message(dm.sender_id, text="Send scores in the format: 'player_1, player_1_score, player_2_score, player_2'. Delete previous score with '!delete.' Check stats of a specific player by sending '!stats player_1'.")
        if validityType == 'RESET12345':
            api.send_direct_message(dm.sender_id, text="CSV file reset.")
            numGames = 0
            del csvMatrix[:]
            updateCSV(csvMatrix)
        if validityType == 'DELETE':
            del csvMatrix[-1]
            numGames -= 1
            api.send_direct_message(dm.sender_id, text="Previous match removed.")
            updateCSV(csvMatrix)
        if validityType == 'false':
            api.send_direct_message(dm.sender_id, text="That is an invalid command. Reply with '!help' for info on how to use this bot.")
        if validityType[:5] == 'stats':
            statString=''
            name = validityType.replace(validityType[:5], '')
            if name in playerList:
                statString = 'Player stats on '+name.title()+'\n\nPlayed: '+str(
                    sum(countWL(name)))+'\nWon: '+str(countWL(name)[0])+'\nLost: '+str(
                        countWL(name)[1])+'\nWin %: '+percentages(name)[0]+'\nGoals For: '+str(
                            goals(name)[0])+'\nGoals Against: '+str(goals(
                                name)[1])+'\nGoal Difference: '+str(goals(
                                    name)[0]-goals(name)[1])
                api.send_direct_message(dm.sender_id, text=statString)
            else:
                api.send_direct_message(dm.sender_id, text='That player does not exist in the database.')                
    writeinIDs()

# Compile all stats in the stats CSV file.        
compileStats()
