
from django.shortcuts import render
import sys
from . forms import RadioForm

from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.personalizer import PersonalizerClient
from azure.cognitiveservices.personalizer.models import RankableAction,RankedAction ,RewardRequest, RankRequest
import pandas as pd
import csv
import datetime
import requests
import pyodbc
import webbrowser

def base1(request):
    return render(request, 'base.html')

def button(request):
    return render(request, 'home.html')

def logout(request):
    return render(request, 'logout.html')

def register(request):
    return render(request, 'register.html')

def executeQuery(url, ontology, token, query):
    if not url.endswith("/"):
       url += "/"
    post_data = {'ontology_name': ontology, 'query': query}
    headers = {'Content-Type': 'application/json', 'x-api-key': token}
    response = requests.post(url + "timbr/api/query/", headers = headers, json = post_data, verify = False)
    response_data = response.json()
    if response_data['status'] == 'success':
        df = pd.DataFrame(response_data['data'])
        return df
    else:
        raise Exception("Error in request: " + response_data['data'])

def timbrcall():
    url = "https://cap-env.timbr.ai" # http://<hostname> or https://<hostname>
    ontology = "personalizerpoc" # ontology name
    token = "tk_fee921d10dbb8127b750959f97ab9be5262380f57845e4fa10f14a75e750a978" # user token
    query = """SELECT DISTINCT 
        `account_id` AS `Account_ID`, 
        `cards_account_id[cards].type_of_card` AS `Card_Assigned`,
        `annual_income` AS `Annual_Income`,  
        `~zipcode[zipcode].per_capita_income_zipcode` AS `Avg_Income_In_Zip`,
        `birth_year` AS `Birth_Year`, 
        `bussiness_owner` AS `Bus_Owner`, 
        `current_age` as `Current_Age`, 
        `existing_customer` AS `Customer_Ind`, 
        `fico_score` AS `Credit_Scope`, 
        `gender` AS `Gender`, 
        `highnetworth` AS `HNI_Customer`, 
        `home_owner` AS `Home_Owner`, 
        `incarcinated` AS `Incarcerated`, 
        `last_time_when_card_was_purchased` AS `Last_Card_Opened`, 
        `~account_id[logins].login_duration` AS `Login_Duration`, 
        `~account_id[logins].login_time` AS `Login_Time`, 
        `num_credit_cards` AS `Num_Cards`, 
        `retirement_age` AS `Retirement_Age`, 
        `total_debt` AS `Total_Debt`, 
        `zipcode` AS `Zipcode`, 
        `person_name` AS `Customer_Name`,
         `address` AS `Address`,
         `apartment` AS `Apartment`,
          `city` AS `City`,
           `state` AS `State`
    FROM `dtimbr`.`customer`
    where 
    --account_id ='708082087' AND
    `cards_account_id[cards].type_of_card`<>'None'
    --LIMIT 10"""

    response = executeQuery(url, ontology, token, query)
    print(response)
    response=response.dropna(subset='Card_Assigned')
    #response=response[response['Card_Assigned']!='None']
    #print(response['Card_Assigned'].unique())
    return response

# get actions and their features

def get_actions(actions_and_features):
    res = []
    for action_id, feat in actions_and_features.items():
        action = RankableAction(id=action_id, features=[feat])
        res.append(action)
    return res

def timbrdf_to_dict_obj(timbrdf):
    # formatting the data
    # currency to float
    timbrdf['Annual_Income'] = timbrdf['Annual_Income'].str.replace('$', '').str.replace(',', '')
    timbrdf['Annual_Income'] = timbrdf['Annual_Income'] .astype(float)
    timbrdf['Avg_Income_In_Zip'] = timbrdf['Avg_Income_In_Zip'].str.replace('$', '').str.replace(',', '')
    timbrdf['Avg_Income_In_Zip'] = timbrdf['Avg_Income_In_Zip'].astype(float)
    timbrdf['Total_Debt'] = timbrdf['Total_Debt'].str.replace('$', '').str.replace(',', '')
    timbrdf['Total_Debt'] = timbrdf['Total_Debt'].astype(float)
    # year to int
    timbrdf['Birth_Year'] = timbrdf['Birth_Year'].str.strip()
    timbrdf['Birth_Year'] = timbrdf['Birth_Year'].astype(int)
    # removing white spaces and making uniform string
    timbrdf['Bus_Owner'] = timbrdf['Bus_Owner'].str.strip()
    timbrdf['Bus_Owner'] = timbrdf['Bus_Owner'].str.title()
    timbrdf['Customer_Ind'] = timbrdf['Customer_Ind'].str.strip()
    timbrdf['Customer_Ind'] = timbrdf['Customer_Ind'].str.title()
    timbrdf['HNI_Customer'] = timbrdf['HNI_Customer'].str.strip()
    timbrdf['HNI_Customer'] = timbrdf['HNI_Customer'].str.title()
    timbrdf['Home_Owner'] = timbrdf['Home_Owner'].str.strip()
    timbrdf['Home_Owner'] = timbrdf['Home_Owner'].str.title()
    timbrdf['Incarcerated'] = timbrdf['Incarcerated'].str.strip()
    timbrdf['Incarcerated'] = timbrdf['Incarcerated'].str.title()
    timbrdf['Incarcerated'] = timbrdf['Incarcerated'].str.strip()
    timbrdf['Incarcerated'] = timbrdf['Incarcerated'].str.title()

    timbrdf['context_features'] = timbrdf.iloc[:,2:].to_dict('records')
    data = timbrdf[['Account_ID','Card_Assigned','context_features']].to_dict(orient='records')
    return data

def external(request):
    global acct_id, user_data, Account_ID, Card_Assigned, Annual_Income, Birth_Year,\
        Zipcode, actionid, eventid, actual_card, prob_list, client,account_id, \
        Total_Debt, Home_Owner, Bus_Owner, Customer_Name, Address, Apartment, \
        City, State, Current_Age, phone, email

    if request.method == "POST":
        acct_id = request.POST.get('param')
        pass_id = request.POST.get('param1')
        print(acct_id)
        print(pass_id)

        if pass_id == 'capgemini':
            print('login successful')
            # extract the data from Timbr.
            timbrdf = timbrcall()
            timbrdf1 = timbrdf.loc[timbrdf['Account_ID'] == acct_id]
            # print(timbrdf1)
            user_data = timbrdf_to_dict_obj(timbrdf1)
            print(user_data)

            for i in user_data:
                Account_ID = (i['Account_ID'])
                Card_Assigned = (i['Card_Assigned'])
                Annual_Income = (i['context_features']['Annual_Income'])
                Birth_Year = (i['context_features']['Birth_Year'])
                Zipcode = (i['context_features']['Zipcode'])
                Total_Debt = (i['context_features']['Total_Debt'])
                Home_Owner = (i['context_features']['Home_Owner'])
                Bus_Owner = (i['context_features']['Bus_Owner'])
                Customer_Name = (i['context_features']['Customer_Name'])
                Address = (i['context_features']['Address'])
                Apartment = (i['context_features']['Apartment'])
                City = (i['context_features']['City'])
                State = (i['context_features']['State'])
                Current_Age = (i['context_features']['Current_Age'])
                break

            endpoint = "https://hyperpersonalizerpoc.cognitiveservices.azure.com/"
            key = "bc343f1d5e22457994f787ddfdb6a1db"
            client = PersonalizerClient(endpoint, CognitiveServicesCredentials(key))

            # The list of actions to be ranked with metadata associated for each action.
            actions_and_features = {
                "Rewards card": {
                    "Annual_Income": 60000 - 99000,
                    "Home_Owner": "No"
                },
                "Business Card": {
                    "Bus_Owner": "Yes",
                    "HNI_Customer": "No"
                },
                "Business Premium": {
                    "Bus_Owner": "Yes",
                    "HNI_Customer": "Yes"
                },
                "Luxury Card": {
                    "Bus_Owner": "No",
                    "HNI_Customer": "Yes",
                    "Home_Owner": "Yes"
                },
                "Platinum Card": {
                    "Bus_Owner": "No",
                    "HNI_Customer": "Yes",
                    "Home_Owner": "No"
                },
                "Student Card": {
                    "Current_Age": 18 - 21,
                    "Annual_Income": "0-30000"
                }
            }
            actions = get_actions(actions_and_features)

            def rank_call(actions, context):
                rank_request = RankRequest(actions=actions, context_features=[context])
                try:
                    rank_response = client.rank(rank_request=rank_request)
                    return rank_response
                except Exception as e:
                    print(e.message)

            for data in user_data:
                account_id = data['Account_ID']
                context = data["context_features"]
                print("Account id: " + str(account_id))
                print("*" * 15 + "Sending Rank Event" + "*" * 15)
                rank_response = rank_call(actions, context)
                if not rank_response:
                    # rank call is failing
                    break
                print("Rank API response:")
                prob_list = [{i.id: i.probability} for i in rank_response.ranking]
                print(prob_list)
                eventid = rank_response.event_id
                actionid = rank_response.reward_action_id
                print(eventid)
                print("Rank Response event_id is : " + eventid)
                print("recommended card is : " + actionid)
                actual_card = data["Card_Assigned"]
                print(data)

                phone = 'xxx-xxx-xxxx'
                email = 'xyz@gmail.com'

            return render(request, 'new.html', {'data1': Account_ID, 'data2': Birth_Year, 'data3': Card_Assigned,
                                                'data4': Zipcode, 'data5': Annual_Income, 'data6': actionid,
                                                'data7': Total_Debt, 'data8': Home_Owner, 'data9': Bus_Owner,
                                                'data10': Customer_Name, 'data11': Address, 'data12': Apartment,
                                                'data13': City, 'data14': State, 'data15': Current_Age,
                                                'data16': phone, 'data17': email})
        else:
            out1 = "Incorrect ID or Password"
            print(out1)
            return render(request, "home.html",{'dataout': out1})

    return render(request, 'new.html', {'data1': Account_ID, 'data2': Birth_Year, 'data3': Card_Assigned,
                                                'data4': Zipcode, 'data5': Annual_Income, 'data6': actionid,
                                                'data7': Total_Debt, 'data8': Home_Owner, 'data9': Bus_Owner,
                                                'data10': Customer_Name, 'data11': Address, 'data12': Apartment,
                                                'data13': City, 'data14': State, 'data15': Current_Age,
                                                'data16': phone, 'data17': email})

def hyper(request):
    global reward_score, eventid, reward_data, user_data, users_reward_data, current_time

    def reward_call(eventid, reward_score):
        # rank_request = RankRequest(actions=actions, context_features=[context])
        try:
            client.events.reward(event_id=eventid, value=reward_score)
        except Exception as e:
            print(e.message)

    if request.method == 'POST':
        form = RadioForm(request.POST)
        if form.is_valid():
            selected_choice = form.cleaned_data['radio_choice']
            print(selected_choice)

            if selected_choice == 'Yes':
                reward_score = 1.0
                out2 = "Thanks for considering the recommended card"
                print(out2)
                print('yes button pressed')
                print(reward_score)
            elif selected_choice == 'No':
                reward_score = 0.0
                out2 = "Thanks for providing your feedback. Will work for new recommendation."
                print(out2)
                print('no button pressed')
                print(reward_score)
            print(eventid)

            print("*" * 15 + "Sending Reward event" + "*" * 15)
            reward_call(eventid, reward_score)
            print("A reward score of", reward_score, "was sent to Personalizer.")
            print("*" * 15 + "End of  this event" + "*" * 15)
            users_reward_data = []
            current_time = datetime.datetime.now()
            reward_data = [account_id, eventid, actual_card, actionid, prob_list[0][actionid], current_time,
                           reward_score]
            users_reward_data.append(reward_data)
            # print(users_reward_data)

            # SYNAPSE - Connection String:
            conn_str = (
                r'DRIVER={ODBC Driver 18 for SQL Server};'
                r'SERVER=tcp:hyperpersonalize.sql.azuresynapse.net;'
                r'DATABASE=Personalizerpool;'
                r'UID=sqladminuser;'
                r'PWD=Capgemini@123;'
                r'PORT=1433;'
                r'Trusted_Connection=No;'
            )
            # SYNAPSE - Write the reward score data back into SYNAPSE table.
            with pyodbc.connect(conn_str) as conn:
                conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin1')
                conn.setencoding('latin1')
                with conn.cursor() as cursor:
                    query = "INSERT INTO dbo.user_reward (Account_ID,Event_id,Actual_card,Recommended_card,Probability,Timestamp, reward_score) VALUES (?,?,?,?,?,?,?)"
                    for record in users_reward_data:
                        cursor.execute(query, record)

            return render(request, 'home1.html', {'data1': Account_ID, 'data2': Birth_Year, 'data3': Card_Assigned,
                                                'data4': Zipcode, 'data5': Annual_Income, 'data6': actionid,
                                                'data7': Total_Debt, 'data8': Home_Owner, 'data9': Bus_Owner,
                                                'data10': Customer_Name, 'data11': Address, 'data12': Apartment,
                                                'data13': City, 'data14': State, 'data15': Current_Age,
                                                'data16': phone, 'data17': email, 'dataout': out2})

    else:
        form = RadioForm()
    return render(request, 'new.html', {'form': form})
