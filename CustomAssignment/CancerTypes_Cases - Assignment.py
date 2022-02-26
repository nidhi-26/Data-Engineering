import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import numpy as np
import matplotlib.pyplot as plt

# Base Website URL
url = "https://seer.cancer.gov"

# HTML Content of Base URL Web Page for StatFacts
html_data  = requests.get(url + "/statfacts/").text

# Applying HTML Parser
soup = BeautifulSoup(html_data, "html.parser")

# Fetching Navigation URLs from Anchor tag and href attribute
navUrlList = []
for row in soup.find_all('a'):
    link = row.get("href")
    if (link != None and link.find("statfacts/html") != -1):
        navUrlList.append(link)

# navUrlSet contains all the Urls that needs to navigated
navUrls = sorted(set(navUrlList))
navUrls.remove('/statfacts/html/common.html')
navUrls.remove('/statfacts/html/all.html')


navUrlLater = ('/statfacts/html/common.html', '/statfacts/html/all.html')
#print(navUrls, navUrlLater)

# Column Variables
columnsTrendInAgeAdjustedIncidenceAndMortalityRates = ['Cancer Type', 'Year', 'SEER-9(Observed)', 'SEER-9(Modeled)', 'SEER-13(Observed)', 'SEER-13(Modeled)', 'Death Rate-US(Observed)', 'Death Rate-US(Modeled)', '5-Year Relative Survival SEER-9(Observed)', '5-Year Relative Survival SEER-9(Modeled)']
columnsPercentByAgeGroup = ['Cancer Type', '< 20', '20 to 34', '35 to 44', '45 to 54', '55 to 64', '65 to 74', '75 to 84', '> 84']
columnsRateByRaceEthnicitySex = ['Cancer Type', 'Gender', 'All Races', 'White', 'Black', 'Asian/Pacific Islander', 'American Indian/Alaska Native', 'Hispanic', 'Non-Hispanic']

# Data variables
cancerTypes = []
rateOfNewCasesByRaceEthnicitySex = pd.DataFrame(columns=columnsRateByRaceEthnicitySex)
rateOfDeathCasesByRaceEthnicitySex = pd.DataFrame(columns=columnsRateByRaceEthnicitySex)
percentOfNewCasesByAgeGroup = pd.DataFrame(columns=columnsPercentByAgeGroup)
percentOfDeathsByAgeGroup = pd.DataFrame(columns=columnsPercentByAgeGroup)
trendInAgeAdjustedIncidenceAndMortalityRates = pd.DataFrame(columns=columnsTrendInAgeAdjustedIncidenceAndMortalityRates)


def getTableData(table, colNames, cancerType):
    finalData = pd.DataFrame(columns=colNames)
    for row in table.find_all('tr'):
        dataTemp = [cancerType]
        for col in row.find_all('td'):
            dataTemp.append(col.get_text())
        if (len(dataTemp) == len(colNames)):
            newRow = pd.DataFrame([dataTemp], columns=colNames)
            finalData = pd.concat([finalData, newRow], ignore_index=True)
    finalData = finalData.replace('-', np.nan)
    finalData.replace(regex=['%'], value='', inplace=True)

    return finalData


def getTableDataWithGender(table, colNames, cancerType, gender):
    finalData = pd.DataFrame(columns=colNames)
    dataTemp = [cancerType, gender]
    for col in table.find_all('td'):
        dataTemp.append(col.get_text() if re.match(r"[0-9]+", col.get_text()) else np.nan)    
    if (len(dataTemp) == len(colNames)):
        newRow = pd.DataFrame([dataTemp], columns=colNames)
        finalData = pd.concat([finalData, newRow], ignore_index=True)
    finalData = finalData.replace('-', np.nan)
    finalData.replace(regex=['%'], value='', inplace=True)

    return finalData


def getTableDataAgeBased(table, colNames, cancerType):
    finalData = pd.DataFrame(columns=colNames)
    dataTemp = [cancerType]
    for col in table.find_all('td')[1::2]:
        dataTemp.append(col.get_text())    
    if (len(dataTemp) == len(colNames)):
        newRow = pd.DataFrame([dataTemp], columns=colNames)
        finalData = pd.concat([finalData, newRow], ignore_index=True)
    finalData = finalData.replace('-', np.nan)
    finalData.replace(regex=['%'], value='', inplace=True)

    return finalData


for navUrl in navUrls:
    html_data = requests.get(url + navUrl).text
    soup = BeautifulSoup(html_data, "html.parser")

    title = soup.find('h1').text.split(': ')[1].strip()
    cancerTypes.append(title)

    
    #Fetching data for "Trends in Age-adjusted Incidence and Mortality Rates" for all Cancer Tyoes
    tableTag = soup.find('table', {'id': 'scrapeTable_01'})
    newData = getTableData(tableTag, columnsTrendInAgeAdjustedIncidenceAndMortalityRates, title)
    trendInAgeAdjustedIncidenceAndMortalityRates = pd.concat([trendInAgeAdjustedIncidenceAndMortalityRates, newData], ignore_index=True)
    
    
    tableDivs = soup.find_all('div', {'class': 'statWrap'})
    for tableDiv in tableDivs:
        tableTitle = tableDiv.find('strong').get_text().strip()[:tableDiv.find('strong').get_text().strip().find(':')] if tableDiv.find('strong') != None else ""
        
        # Fetching data for "Rate of New Cases per 100,000 Persons by Race/Ethnicity" for all Cancer Types
        if (tableTitle.find('Rate of New Cases per 100,000 Persons by Race/Ethnicity') != -1):
            tables = tableDiv.find_all('table')
            for i in range(0, 2):
                if (i == 0):
                    gender = 'Male'
                else:
                    gender = 'Female'

                newData = getTableDataWithGender(tables[i], columnsRateByRaceEthnicitySex, title, gender)
                rateOfNewCasesByRaceEthnicitySex = pd.concat([rateOfNewCasesByRaceEthnicitySex, newData], ignore_index=True)

        
        # Fetching data for "Death Rate per 100,000 Persons by Race/Ethnicity" for all Cancer Types
        if (tableTitle.find('Death Rate per 100,000 Persons by Race/Ethnicity') != -1):
            tables = tableDiv.find_all('table')
            for i in range(0, 2):
                if (i == 0):
                    gender = 'Male'
                else:
                    gender = 'Female'

                newData = getTableDataWithGender(tables[i], columnsRateByRaceEthnicitySex, title, gender)
                rateOfDeathCasesByRaceEthnicitySex = pd.concat([rateOfDeathCasesByRaceEthnicitySex, newData], ignore_index=True)

        
        # Fetching data for "Percent of New Cases by Age Group" for all Cancer Types
        if (tableTitle.find('Percent of New Cases by Age Group') != -1):
            tables = tableDiv.find_all('table')
            newData = getTableDataAgeBased(tables[0], columnsPercentByAgeGroup, title)
            percentOfNewCasesByAgeGroup = pd.concat([percentOfNewCasesByAgeGroup, newData], ignore_index=True)

        
        # Fetching data for "Percent of Deaths by Age Group" for all Cancer Types
        if (tableTitle.find('Percent of Deaths by Age Group') != -1):
            tables = tableDiv.find_all('table')
            newData = getTableDataAgeBased(tables[0], columnsPercentByAgeGroup, title)
            percentOfDeathsByAgeGroup = pd.concat([percentOfDeathsByAgeGroup, newData], ignore_index=True)
            


# Since all the datatypes are text now, changing it int or float for analysis

#   trendInAgeAdjustedIncidenceAndMortalityRates
trendInAgeAdjustedIncidenceAndMortalityRates['Year'] = trendInAgeAdjustedIncidenceAndMortalityRates['Year'].astype(int)
for c in trendInAgeAdjustedIncidenceAndMortalityRates.columns[2:]:
    trendInAgeAdjustedIncidenceAndMortalityRates[c] = trendInAgeAdjustedIncidenceAndMortalityRates[c].astype(float)

#   rateOfNewCasesByRaceEthnicitySex
for c in rateOfNewCasesByRaceEthnicitySex.columns[2:]:
    rateOfNewCasesByRaceEthnicitySex[c] = rateOfNewCasesByRaceEthnicitySex[c].astype(float)

#   rateOfDeathCasesByRaceEthnicitySex
for c in rateOfDeathCasesByRaceEthnicitySex.columns[2:]:
    rateOfDeathCasesByRaceEthnicitySex[c] = rateOfDeathCasesByRaceEthnicitySex[c].astype(float)

#   percentOfNewCasesByAgeGroup
for c in percentOfNewCasesByAgeGroup.columns[1:]:
    percentOfNewCasesByAgeGroup[c] = percentOfNewCasesByAgeGroup[c].astype(float)

#   percentOfDeathsByAgeGroup
for c in percentOfDeathsByAgeGroup.columns[1:]:
    percentOfDeathsByAgeGroup[c] = percentOfDeathsByAgeGroup[c].astype(float)


print(cancerTypes)
print(trendInAgeAdjustedIncidenceAndMortalityRates)
print(rateOfNewCasesByRaceEthnicitySex)
print(rateOfDeathCasesByRaceEthnicitySex)
print(percentOfNewCasesByAgeGroup)
print(percentOfDeathsByAgeGroup)



# Ploting charts

def maxCancerBarPlot(df, col, title):
    df = df.sort_values(by=col, ascending=False)
    plt.bar(df['Cancer Type'], df[col])
    plt.xticks(rotation=90)
    plt.title(title)
    plt.show()


def stackedBarChart(df, title):
    df.plot(x='Cancer Type', kind='bar', stacked=True, title=title)
    plt.show()


def lineChartTrendChart(df, col, title):
    for c in col:
        plt.plot(df['Cancer Type'], df[c], marker='o', label=c)
    plt.title(title)
    plt.xlabel('Cancer Type')
    plt.xticks(rotation=90)
    plt.grid(True)
    plt.show()

def groupedBarChart(df, title, col):
    x = np.arange(len(df['Cancer Type']))
    width = 0.5
    fig, ax = plt.subplots()
    rects = []
    for i, c in enumerate(col):
        if (i % 2 == 1):
            rects.append(ax.bar(x - width*(i)/len(col), df[c], width/len(col)*2, label=c))
        else:
            rects.append(ax.bar(x + width*(i+1)/len(col), df[c], width/len(col)*2, label=c))
    ax.set_xticks(x, df['Cancer Type'])
    ax.set_title(title)
    ax.legend()
    plt.xticks(rotation=90)
    plt.show()

def boxPlotChart(df, col, title):
    df.boxplot(column=col, rot=45, grid=False)
    plt.title(title)
    plt.show()



#Figure_1
stackedBarChart(percentOfNewCasesByAgeGroup, 'Percent of New Cases by Age Group')



#Figure_2
lineChartTrendChart(percentOfDeathsByAgeGroup, ['< 20', '20 to 34', '35 to 44', '45 to 54', '55 to 64', '65 to 74', '75 to 84', '> 84'], 'Percent of Deaths by Age Group')



# Figure_3
dataTemp = rateOfNewCasesByRaceEthnicitySex[rateOfNewCasesByRaceEthnicitySex['Gender'] == 'Male']
maxCancerBarPlot(dataTemp, 'All Races', 'Rate of New Cases amongst Males (All Races)')



# Figure_4
dataTemp = rateOfDeathCasesByRaceEthnicitySex[rateOfDeathCasesByRaceEthnicitySex['Gender'] == 'Female']
maxCancerBarPlot(dataTemp, 'Black', 'Rate of New Cases amongst Females (Black)')



# Figure_5
dataTemp = rateOfNewCasesByRaceEthnicitySex.groupby('Cancer Type').sum().reset_index()
maxCancerBarPlot(dataTemp, 'White', 'Rate of New Cases amongst White irrespective of gender')



# Figure_6
dataTemp = trendInAgeAdjustedIncidenceAndMortalityRates.groupby('Cancer Type').sum().reset_index()
groupedBarChart(dataTemp, 'Observed & Modeled data for SEER 9 for all Cancer Types', ['SEER-9(Observed)', 'SEER-9(Modeled)', 'SEER-13(Observed)', 'SEER-13(Modeled)'])



# Figure_7
dataTemp = trendInAgeAdjustedIncidenceAndMortalityRates.groupby('Cancer Type').sum().reset_index()
groupedBarChart(dataTemp, 'Observed & Modeled data for SEER 9 for all Cancer Types', ['SEER-9(Observed)', 'SEER-9(Modeled)'])



# Figure_8
dataTemp = rateOfNewCasesByRaceEthnicitySex.groupby('Cancer Type').sum().reset_index()
boxPlotChart(dataTemp, ['All Races', 'White', 'Black', 'Asian/Pacific Islander', 'American Indian/Alaska Native', 'Hispanic', 'Non-Hispanic'], 'Rate of New Cases for Cancer (any type)')


# Figure_9
dataTemp = trendInAgeAdjustedIncidenceAndMortalityRates.groupby('Year').sum().reset_index()
boxPlotChart(dataTemp, ['SEER-9(Observed)', 'SEER-9(Modeled)', 'SEER-13(Observed)', 'SEER-13(Modeled)', 'Death Rate-US(Observed)', 'Death Rate-US(Modeled)'], '')


