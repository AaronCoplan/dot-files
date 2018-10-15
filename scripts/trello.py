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
    (lists, cards) = loadBoardData('To Do')

    overdueList = filterToListX(lists, 'Overdue')
    todayList = filterToListX(lists, 'Today')
    next7DaysList = filterToListX(lists, 'Next 7 Days')

    overdueCards = sortByDate(list(filter(isCardOverdue, cards)))
    moveCardsToList(overdueCards, overdueList, position='top')

    cards = subtractLists(cards, overdueCards)

    dueTodayCards = sortByDate(list(filter(isCardDueToday, cards)))
    moveCardsToList(dueTodayCards, todayList, position='top')

    cards = subtractLists(cards, dueTodayCards)

    dueNext7DaysCards = sortByDate(list(filter(isCardDueNext7Days, cards)))
    moveCardsToList(dueNext7DaysCards, next7DaysList, position='top')

    cards = subtractLists(cards, dueTodayCards)

    opsCompleted = len(overdueCards) + len(dueTodayCards) + len(dueNext7DaysCards)
    print('{} operations completed.  The following cards are overdue or due soon:'.format(opsCompleted))
    for card in reversed(sortByDate(overdueCards + dueTodayCards)):
        print('-  {}'.format(card['name']))

def sortByDate(cards):
    return sorted(cards, key=lambda card: card['due'], reverse=True)

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

def loadBoardData(boardName):
    jsonBoards = makeRequest('/members/me/boards')
    board = list(filter(lambda board: board['name'] == boardName, jsonBoards))
    if board is None:
        raise Exception('Could not find To Do board')
    else:
        board = board[0]

    jsonLists = makeRequest('/boards/{}/lists'.format(board['id']), params="?filter=open&cards=open")
    jsonCards = makeRequest('/boards/{}/cards/open'.format(board['id']))
    return (jsonLists, jsonCards)

def parseDueDateAsLocalDateTime(dueDateStr):
    date = datetime.fromisoformat(dueDateStr.replace('Z', ''))
    date = date.replace(tzinfo=timezone.utc)
    return date.astimezone()

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
