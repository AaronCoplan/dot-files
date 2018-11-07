#!/usr/bin/env python3

import sys
if sys.version_info[0] < 3:
    raise Exception('Must be using Python 3')

import json
import requests

from datetime import datetime, timezone, timedelta

TOKEN = None
KEY = None
CURRENT_DATE_TIME = datetime.now().astimezone()

def main():
    loadCreds()
    (lists, cards, staleLabel) = loadBoardData('To Do')

    overdueList = filterToListX(lists, 'Overdue')
    todayList = filterToListX(lists, 'Today')
    next7DaysList = filterToListX(lists, 'Next 7 Days')
    backburnerList = filterToListX(lists, 'Backburner')

    overdueCards = sortByDate(list(filter(isCardOverdue, cards)))
    moveCardsToList(overdueCards, overdueList, position='top')

    cards = subtractLists(cards, overdueCards)

    dueTodayCards = sortByDate(list(filter(isCardDueToday, cards)))
    moveCardsToList(dueTodayCards, todayList, position='top')

    cards = subtractLists(cards, dueTodayCards)

    dueNext7DaysCards = sortByDate(list(filter(isCardDueNext7Days, cards)))
    moveCardsToList(dueNext7DaysCards, next7DaysList, position='top')

    cards = subtractLists(cards, dueTodayCards)

    overdueOrDoSoonCards = list(reversed(sortByDate(overdueCards + dueTodayCards)))

    staleCards = list(filter(isCardStale, cards))
    staleCardsWithoutLabel = list(filter(lambda card: not cardHasLabel(card, staleLabel), staleCards))
    addLabelToCards(staleCardsWithoutLabel, staleLabel)

    noLongerStaleCards = list(filter(lambda card: cardHasLabel(card, staleLabel), subtractLists(cards, staleCards)))
    removeLabelFromCards(noLongerStaleCards, staleLabel)

    backburnerCards = sortByDate(list(filter(lambda card: card['due'] is not None, getCardsForList(backburnerList))))
    moveCardsToList(backburnerCards, backburnerList, position='top')

    printHeader('The following {} cards are overdue or due soon:'.format(len(overdueOrDoSoonCards)))
    for card in overdueOrDoSoonCards:
        print('-  {}'.format(card['name']))

    printHeader("Marked the following {} cards as stale:".format(len(staleCardsWithoutLabel)))
    for card in staleCardsWithoutLabel:
        print('- {}'.format(card['name']))

    printHeader('Removed the stale label from the following {} cards:'.format(len(noLongerStaleCards)))
    for card in noLongerStaleCards:
        print('- {}'.format(card['name']))

def printHeader(string):
    dashString = ''
    for _ in range(len(string) + 4):
        dashString += '-'
    print(dashString)
    print('| {} |'.format(string))
    dashString = ''
    for _ in range(len(string) + 4):
        dashString += '-'
    print(dashString)

def sortByDate(cards):
    return sorted(cards, key=lambda card: card['due'], reverse=True)

def isCardStale(card):
    staleThresholdDate = CURRENT_DATE_TIME + timedelta(days=-10)
    creationDate = parseDateCreated(card)

    if creationDate >= staleThresholdDate:
        return False

    jsonActions = makeRequest('/cards/{}/actions'.format(card['id']), params='?limit=1')
    if len(jsonActions) == 0:
        return True
    lastAction = jsonActions[0]
    return parseDueDateAsLocalDateTime(lastAction['date']) < staleThresholdDate and card['due'] is None

def isCardDueNext7Days(card):
    if card['due'] is None:
        return False
    return parseDueDateAsLocalDateTime(card['due']).date() < (CURRENT_DATE_TIME + timedelta(days=7)).date()

def isCardDueToday(card):
    if card['due'] is None:
        return False
    return parseDueDateAsLocalDateTime(card['due']).date() == CURRENT_DATE_TIME.date()

def isCardOverdue(card):
    if card['due'] is None:
        return False
    return parseDueDateAsLocalDateTime(card['due']) < CURRENT_DATE_TIME

def getCardsForList(lst):
    return makeRequest('/lists/{}/cards'.format(lst['id']))

def loadBoardData(boardName):
    jsonBoards = makeRequest('/members/me/boards')
    board = list(filter(lambda board: board['name'] == boardName, jsonBoards))
    if board is None or len(board) == 0:
        raise Exception('Could not find To Do board')
    else:
        board = board[0]

    jsonLists = makeRequest('/boards/{}/lists'.format(board['id']), params="?filter=open&cards=open")
    jsonCards = []
    for jsonList in jsonLists:
        jsonCards += jsonList['cards']

    jsonLabels = makeRequest('/boards/{}/labels'.format(board['id']))
    staleLabel = list(filter(lambda label: label['name'] == 'STALE', jsonLabels))
    if staleLabel is None or len(staleLabel) == 0:
        raise Exception('Could not find STALE label')
    else:
        staleLabel = staleLabel[0]

    return (jsonLists, jsonCards, staleLabel)

def parseDueDateAsLocalDateTime(dueDateStr):
    date = datetime.fromisoformat(dueDateStr.replace('Z', ''))
    date = date.replace(tzinfo=timezone.utc)
    return date.astimezone()

def parseDateCreated(card):
    return datetime.fromtimestamp(int(card['id'][0:8],16)).astimezone()

def cardHasLabel(card, label):
    return label['id'] in card['idLabels']

def removeLabelFromCards(cards, label):
    for card in cards:
        removeLabelFromCard(card, label)

def removeLabelFromCard(card, label):
    removeLabelId = label['id']
    if removeLabelId in card['idLabels']:
        card['idLabels'] = list(filter(lambda id: id != removeLabelId, card['idLabels']))
        labelsParam = ','.join(card['idLabels'])
        makeRequest('/cards/{}'.format(card['id']), '?idLabels={}'.format(labelsParam), 'PUT')

def addLabelToCards(cards, label):
    for card in cards:
        addLabelToCard(card, label)

def addLabelToCard(card, label):
    newLabelId = label['id']
    if newLabelId not in card['idLabels']:
        card['idLabels'].append(newLabelId)
        labelsParam = ','.join(card['idLabels'])
        makeRequest('/cards/{}'.format(card['id']), '?idLabels={}'.format(labelsParam), 'PUT')

def moveCardsToList(cards, newList, position=None):
    for card in cards:
        moveCardToList(card, newList, position=position)

def moveCardToList(card, newList, position):
    if position is None:
        makeRequest('/cards/{}'.format(card['id']), '?idList={}'.format(newList['id']), 'PUT')
    else:
        makeRequest('/cards/{}'.format(card['id']), '?idList={}&pos={}'.format(newList['id'], position), 'PUT')

def filterToListX(lists, filterName):
    obj = list(filter(lambda list: list['name'] == filterName, lists))
    if obj is None:
        raise Exception('Could not find list {}'.format(filterName))
    else:
        return obj[0]

def subtractLists(bigList, subList):
    return [x for x in bigList if x not in subList]

def loadCreds():
    global TOKEN, KEY
    with open('./trellocreds.json', 'r+') as f:
        jsonString = f.read()
        jsonObj = json.loads(jsonString)
        TOKEN = jsonObj['token']
        KEY = jsonObj['key']

def makeRequest(url, params='', method='GET'):
    baseUrl = 'https://api.trello.com/1'
    if params == '':
        auth = '?key={}&token={}'.format(KEY, TOKEN)
    else:
        auth = '&key={}&token={}'.format(KEY, TOKEN)
    requestUrl = '{}{}{}{}'.format(baseUrl, url, params, auth)
    if method == 'GET':
        response = requests.get(requestUrl)
        return response.json()
    elif method == 'PUT':
        response = requests.put(requestUrl)
        return response.json()
    raise Exception('Unknown Method')

if __name__ == '__main__':
    main()
