###### LIBRARIES
import requests
import csv
import re
import yfinance as yf
from bs4 import BeautifulSoup
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import sys
from tqdm import tqdm
import time
import os

###### SCRIPTS 
import BQ_Interact as BQ
import Scraper as SC
import DB_Management as DB


####### FUNCTIONS ####################################

''' Loading bar
total_iterations = 50
with tqdm(total=total_iterations, desc="Custom Processing", unit="steps", ncols=100) as pbar:
    for _ in range(total_iterations):
        time.sleep(0.1)  # Replace with your actual processing logic
        pbar.update(1)
'''


######### MENU #####################

def action_one():
    print("\nYou have selected Action One.")
    # Implement the logic for Action One here
def action_two():
    print("\nYou have selected Action Two.")
    # Implement the logic for Action Two here
def action_three():
    print("\nYou have selected Action Three.")
    # Implement the logic for Action Three here
def display_menu():
    os.system('clear')
    print("\n" + "*" * 36)
    print("*{:^34}*".format("Welcome to the Main Menu"))
    print("*" * 36)
    print("* {:<32} *".format("1. Add/Create Table"))
    print("* {:<32} *".format("2. Scrape Internet"))
    print("* {:<32} *".format("3. Scrape"))
    print("* {:<32} *".format("4. Exit"))
    print("* {:<32} *".format("5. Total Reset"))
    print("* {:<32} *".format("6. Quit Program"))
    print("*" * 36)

def Menu():
    while True:

        display_menu()
        choice = input("\nEnter your choice (1-6): ")
        if choice == '1':
            DB.establish_Hit()
        elif choice == '2':
            SC.run()
        elif choice == '3':
            action_three()
        elif choice == '4':
            print("\nExiting the program. Goodbye!")
            break
        elif choice == '5':
            print("\nYou have selected 'Total Reset'. This will delete all data and drop all tables. This is intended for testing only.")
            choice = input("\nProceed? (y/N): ")
            if choice == "y" or "Y":
                BQ.wipe()
            elif choice == "n" or "N":
                Menu()
            else:
                print("\nInvalid choice. No action committed.")
                Menu()
        elif choice == '6':
            print("\nYou have selected to quit the program.")
            choice1 = str(input("\nProceed? (y/N): "))
            print(choice1)
            if choice1 == ("y" or "Y"):
                exit()
            elif choice1 == ("n" or "N"):
                #time.sleep(3)
                Menu()
            else:
                print("\nInvalid choice. No action committed.")
                time.sleep(1)
                Menu()
        else:
            print("\nInvalid choice. Please enter a number between 1 and 6.")
            time.sleep(1)
            Menu()

if __name__ == "__main__":
   Menu()
   
