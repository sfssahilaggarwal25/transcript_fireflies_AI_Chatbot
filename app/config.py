import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FIREFLIES_API_URL = "https://api.fireflies.ai/graphql"
    API_KEY = os.getenv("FIREFLIES_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"

# Production level Transcript
CONSTANT_TRANSCRIPT = {
    "data": {
        "transcript": [
            {
            "id": "01KM2DD6MXGSZ4F1QW0BNJE16N",
            "title": "Nolocode meeting with Ashpreet",
            "date": "2026-05-08",
            "sentences": [
                {
                    "text": "Would have been great to like also have gotten these questions before yesterday and had you guys already shared this document with, with what's the name Akash or.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "No, we have to share any kind of document with Akash yet because they just informed us that we can discuss everything with you.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So that.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Because that was the kind of loop that they are informing us then we still have the queries and we need to ask them again and they are asking you.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So that's why we have set up this meeting so that we can discuss everything with you directly",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "also ma'.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Am.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "But we have shared some of the questions with them.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We have not shared this sheet particularly but we have shared directly questions with",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "them they are aware about.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, I think there was some confusion because I think we went back and forth but we didn't understand the actual questions.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Now it seems a bit more clear.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "So usually like ONCA and is really used in the balance sheet and the cash flow forecast.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "I'm trying to see like whether we did use it.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Yeah, no, so I'm looking at onca.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We haven't given long term investments, investment property goodwill.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We haven't given.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, I think we can, we haven't given a forecasted formula for it.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So when you can provide that to us because actually the thing is we are still stuck in these kind of things and we are unable to proceed it further.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So it would be good if you feel like that.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yes, some formulas are required from your end and then you can provide it at your earliest.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay, let's go to the next question.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I can try to give you the formula on this call itself.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And other, my other question is for OCA we have four value in the document.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Like one is prepaid open, new prepaid, prepaid amount and prepaid close.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "OCA will be prepaid closed.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That is telling you the calculation of how to get there from open to close.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So it's pretty paid.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So how we will calculate it like prepare close minus prepaid open for change in oca.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Change in oca it will be what your prepaid close is from the previous month.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So if you're looking at March 2026, you're comparing your March 2026 prepaid close number to February 2026 prepaid close and",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "for January we will take from the previous year.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "December 2025.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So we will take that OC OCA value like in the code, like some of these three.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah, so.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So I think I've given that number as well.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So if you go to inputs, the inputs tab here in this sheet.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "No, no, no, no, no, no, no.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Go back to the other sheet you're on or even.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If you go to inputs.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I think if you go down.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I think this is where he.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Prepaid opening.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you have.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "26 2.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You have the AR balance, inventory balance, AP balance.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, we've added all that in here.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I think we like we have to",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "only take this sub account value.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yes, we gave the balance and then Akash had put in some, some comments right in there because I remember going through this with him in the call a couple of weeks ago.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Just to clarify rhythm.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Actually we need to take into.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "For the oca, we need to take into account for the prepaid close.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "And if you need to calculate for the December 2025, you will need to like take into account all the three other values and add and subtract according to the formula.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Then you will get the value for the December part.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "No, no, no, no, no, no.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Repaid clothes you already have.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You already have the actual number from December 2025.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That's what I'm saying.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "These are from there.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Do you have it to them?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yep.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "They are saying to take this value, this account prepaid expenses which come under code OCA for December 2025 and that value is 262141.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "And for my next question is for earnings not in retained earning as I show you there cash flow, change in earnings not attribute to retained income.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So four changes for actual value.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "We have this formula used in code by your team.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Like change in retain learning and other equity equal to change in other equity plus change in current earning plus change in retained earnings minus these values.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "But you only provide us this code.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "We do not have any formula to how to calculate for forecasting.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Can you show me where that is in the financial statements in the ua?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Change in earnings.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So this is in cash flow, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yep.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "If we have to use the formula used by your team then we need these four values also like change in other equity, change in current earnings, dividends and adjustments like their forecasting values.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So forecasting value for dividends you already have.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "But we don't have change in other equity and change in current earnings.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Can I see which the code that they're referring to if you go to the source documentation where there is.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So change in other equity and change in current earnings.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So the actual Excel with the financial data, which line items are you, are they referring to in the code?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "In the code your team is using this formula.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So which account Classifications are they taking.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "They are taking break for a second.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "They are taking oeq.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Dividend div.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Retained earning RA for adjustment.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "They are taking adjustments.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Can you just write these all down so it's clear to us as well?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "In the document which you created and just write every code in front of the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So then it's.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "It's clear",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "in the formula only.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Can you.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "In the formula, how we are calculating each value Just in the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "In the circular braces.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Just write the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "You can write.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "It.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "So we need to calculate these forecasting values also to calculate this.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Cediv.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So div.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You have.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So can we just put a note that the values you already have.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, so this is already provided.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Adj.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We said we're not doing.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So we're not forecasting adjustments.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "For forecasting.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So that's not applicable.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We also have change in retained earnings.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Then we need these two values.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "And my last query is for fixed assets.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah, Just one second.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Is it ce?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I don't see CE as a classification anyway.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "It is mentioned in the code there ce.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So I don't.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If you look at the document.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I don't.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Is it CE or re?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Are you sure",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "this code in the",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "document,",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Are you able to define the code and find where it's been applied?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Maybe it was renamed in the code.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Obviously we are not aware.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Like are you able to follow that and see how many times it's been used or in which calculation it was used in the code?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "It is used for current earnings prior current running.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "But why is it defined before this or used?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "They are just using this classification code only and they will search it from DB then.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So can you see where they're extracting the.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So we have the db right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And if we can we see what numbers they're extracting for some particular month so we can see where they're deriving the numbers from?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "From the Excel db.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Wait a second.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "I will check.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Prism.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Can you run a query just to find all the data related to CE code only?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yes sir.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "It.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "No, we do not have any count related to that as we will uploading this Excel sheet.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "But in this Excel sheet there is no such code.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So it is also not present in the db.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So they're taking no.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "No numbers.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yep.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So what's the only number taken then?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "It's only taken from oeq.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Is it?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Maybe your team is providing any other Excel sheet using any other Excel sheet.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "No, it's the same one.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I'll check with Ashpreet.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Then There is no such code in Adobe.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "We have this code, but no account related to that.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Okay, so if I, if I take a particular month, what numbers are we using then?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So let's take a number.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Let's take a month like January 2024 for example.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "What are the numbers that it's taking to do the calculation based on this code?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Then we can see which numbers they're taking.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Then they are just taking this code and use this in this function.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "No, no.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So can we take an example to see what numbers are taking and based on the code, let's see what numbers are extracting from the db.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "But in a DB we do not have that account.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah, sorry, rhythm.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "For the full formula they have, they have been taking the OEQ and the adj.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So can you calculate value for one month using the other other other data like change in retained earning another equity or there are other three things also?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "No, can you let them, can you show the numbers for others?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Have you understood algorithm what we are saying?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "What was the tag again?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Pe or ec?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Ce.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So I don't see ce, I see re.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "What if maybe instead of EC they meant equity, they meant equity clause.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Right?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Because.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "And then they're taking the equity open",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "plus the net profit and balance.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "They should have been like ec but then they called it the.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Because if you go back to the question they want to know like what value do they put in the cash flow statement and.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Every month for.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Okay, you guys are trying to calculate the total equity in the balance sheet or what was the question with regard to?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "If you go back to the original, original question inside your document.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "So what's the calculation you after number three.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "After number three for fixed assets.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "No, no, no, no, no.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Change in retaining earning another equity.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "We are using change in other equity.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "No, no, no.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "What's, what's the calculation you're after?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "This is a formula.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "What is the actual calc.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "What are you, what are we calculating?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Earnings.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Not in retained earnings.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Wouldn't that be equity?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Yeah, I will show you in ui.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah, So it's under financing activities.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, just going to the Excel.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So shall we proceed with the next query?",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Just one second.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, let's go to the next query.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We'll come back to these two.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, the next queries.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "For fixed assets, as you mentioned in the sheet, for sub account we need to use PP closing and total depreciation from capex.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "But for actual value for property and equipment or for accumulated depreciation, which code we will refer.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Like under FA code we have four sub Accounts like land and building, plant and machinery, furniture, equipment, or computer equipments.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So all this will come under property and equipments.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Correct.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And for accumulated depreciation, for actual, we have depth code which has amortization and depreciation.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So should we use depth code for that?",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Like I show you, in this financial sheet, we have code dep.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "And DEP has six sub accounts.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Go back to the ui because we shouldn't.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If you go, where are we looking?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "It's balance sheet, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So we shouldn't have accumulated depreciation as a line item here to begin with.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So this accumulated depreciation, this wasn't in Ashpreet's code, which is a question he was asking if you've merged the code.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Because this accumulated depreciation row was never there and never calculated in the output he had produced.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So we should.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We should not have accumulated appreciation.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Your question on property and equipment is, basically, there's four accounts.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "The answer to that, this accumulated depreciation should not be there.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So we shall remove it from the UI as well and we can just focus on the property and equipment for now.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, got it.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "And for fixed asset, the sum of this is fixed asset.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Closing balance.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "My nice.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Accumulated depreciation equal to fixed assets.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So we are not calculating this.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So this means fixed assets is equal to PP closing balance.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Correct.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay,",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "that's all from my side.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So if you go to the top, don't stop sharing.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you had your question on onca, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So for.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So for onca, what you can use is to keep it simple.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You can use the same numbers from the previous year.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So ONCA has three items, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "It has goodwill, investment property, long term investments.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You can use the Same numbers from 2025.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "As your forecasted numbers for now.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So there's only one pending question, right?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Okay,",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Only one pending question, is it?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "That's right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So if you go back to that one pending question.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Just one.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "One second.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Can you share your screen?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "One second, please.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So what's the one pending question that we have?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Not this one rhythm, the third one.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah, yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So if you go to the Excel, because what you're doing is you're calculating your cash flow for your financing activities, go to the Excel and go to the cash flow tab here.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you can see in column J, you have your financing cash flow from financing activities.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You have the formula here.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So if you go into it, You are getting all the numbers right that you have.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "So if you follow it to what it's calculating.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "These are then your rows basically that you'll get that how you're getting your cash flow from financing activities.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Okay, can you repeat that question again?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Go to the Excel, go to the sheet again and then click on the cell on.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Click on the cell.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Okay, now instead of.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Yeah, just click once and then go to the, the top of the bar and then you click on CAPEX that you see F83 or any of the values, just click.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Click on one of them.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Yeah, they're up there.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Up there where you are.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "So he's saying you should basically, if you want to know the exact calculation and where the source data is coming from, when you click there, you should be able to highlight on this sheet where it's coming from and then use that as the same formula to understand the, the value, the output.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Click on it once.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Like click on an entire like CAPEX 32 83.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Maybe pick one.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Click on D83.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "It's not there.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "I think",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "it'll Highlight.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "This is D83, 4.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If you follow the formulas, it gives you all the numbers it's taking, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "As a, as a calculation, there was C67, D67, C83.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If you go, you'll see there about four or five.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right, so it's telling you which rows and what it's taking to derive the number.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So it.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "We are calculating this, this earning like we have retained.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "No, go to the ui.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah,",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "go to the cash flow.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You are calculating financing activities, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Cash flow from financing activities.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you have got all the, the numbers there, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "To do.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "To, to get to your number,",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "All the sub items.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "You're saying that we have this, this and this.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So we will minus.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Then we will calculate financing financing activity.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "We will minus this.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Then we will get change in earning, not attribute to retaining income.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "No, no, no, what I'm saying is from your.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You have sub line items that you can take your calculation from.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That's what I'm saying.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If you follow that formula, you have five, five numbers that it's relating to, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you have all the numbers, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And if you're summing them all up, you get your total, which is your financing activities.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, can you go to Rashid once again?",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Let me just see that formula.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Financial cfa.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Let's just write it down.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right, so let's look at C67 and D67.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Actually write down what?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, so what are C67 and D67?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Why don't you actually write down.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Great, yeah, write down the names, right, basically of what?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "C67 83 +E83F83.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "D67.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "It's new loans here.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "D67 is repayments.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So it's short term debt.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you can see it says short term debt above.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So short term debt repayments.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "D83 owner funding, F83 dividends.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So it's D and then ENF.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And one is external funding.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "External funding and then dividends.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So those are your.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That's your breakdown of how you get to your financing activities.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So what I would recommend if you",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "actually like.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We already calculated change in short term depth and change in long term depth.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Like can you properly.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like we have we like in the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Before calculating the total financial activities.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you are saying that this is the formula and this will be the total value.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "But to calculate the only the change in earning note attribute retained income.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We don't know like which.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Which column we should highlight from which column this or which code we need to take into account to calculate the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Just this part only.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like to calculate total financial activity.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "You guys told that this is the formula and this is the columns you need to take into account.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "But like in the change in earning.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Not every tender.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like with what data?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like we need to calculate this from.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "No, no.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So what I'm saying is your financing activities make up of those five balances.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So there's something.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "There's something that's happened.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Either you've merged the code because these items are not there in what Ashpreet had given.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "This change in earnings not attributed to retained income was never there.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Actually this is the mockup ui.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We can't change to this part.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So it was there before.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Only we haven't changed in the mocked ui.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "It's provided from your side only.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "It was there starting.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "No, no.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So what I'm saying is current uses five items that we've just gone through.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Follow the formulas.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you want to that like in the financial activities.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We should mention those five points here.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Not these ones.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Got it.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So those five points are new loans, short term debt.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "It's owner funding, external funding.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And then you have the last one which was.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Repayments dividends.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Not this one.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "No, no.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, sir.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah, we go.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "There we go.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We have.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We have to use these exact value.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "We have to use like change in new loans or change in loan close or change in dividends.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Like this.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Let me answer.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "You're calculating the cash flow.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you are asking you.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You are calculating the.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Go back to the Excel.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Note the movement for.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "For that particular month.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, it's for the.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "It's for those months.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "What they're saying is you need to take the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Suppose this is the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like this is the value and these are drive from these five values.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And these are the actual values.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So you need to like you need to take into account these actual values.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Get their change in values for every month and then we need to show it over there you have the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "No, no, these are the actual values.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So your actual value.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So for example.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "No, this is forecasted values.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah, yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you're forecasted.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So for your cash flow from financing activities, your forecasted value for Jan 2026 will be 20,000.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Go back to the UI.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, so that will be minus 20,000.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So here in financing activities in blue you will have minus 20,000 and then the breakdown you'll have is.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You'll have that breakdown of what those.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "What those five items are.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "How does minus 20,000 break down from.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, okay, I got it.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Actually I was just trying to say that in here we are showing the change in values.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We are not showing the actual forecasted values.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So it will be not shown as here 20000 it will be subtract.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Suppose we are showing the May value here.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "It will be subtracted first and then that value will be shown here.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Or do you want to show the actual just the forecasted value there only you don't want to show the change values here.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Change in like as we are doing we are subtracting the of the previous month.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Then we're showing here like we have",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "already done for change in short term depth or change in long term depth.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "I mean I. I believe you should be showing the.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "The forecasted values and then the variance is what shows the change.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Correct?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "But yeah, so the variance column like at the last.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "At the end, that's where usually changes.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Yeah, we can do that also.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Sure.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Like for change in short term, long term depth we are using this formula like loan open from depth calculation for Jan 2026 minus December 2025.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Can we do this on WhatsApp?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Simran, are you looking at WhatsApp?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Yes, yes.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So that's what we are proposing.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Okay, you have shared an example.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Okay, let me share that with my team so that they can have a look at it.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Just a second.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "I am doing it on a quality.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So I mean the example is Excel, right?",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "The current calculation shows it's 20,000 and that's how it ended up as 20,000 because of the addition or subtraction of Those items.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "So instead of writing the line as change in,",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "we can show directly.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We can show directly the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And then the variance column is your change.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you can see what that number was from this month versus last month.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And then that is your change in number.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You subtracting the current.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Current.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Current month's number from the previous month's number.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yep, we have got it.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "The screenshot, ma', am, I've shared.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Can you please check the group first?",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "No, no, local group.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We don't want to show rhythm changes, actual forecasted values and the variance will show what are the changes values.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "And like we have to do it",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "for all of this.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Like",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "we are also showing change in other current liabilities, change in account payables, change in inventories.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "So we have to show forecasted value or change in values.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "For under cash flow.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "It is like for operating activities, like change in account payables, change in other current liabilities, change in account receivables.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "No, that, no, that is correct.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "For operating activities that you have to show the change change.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That is correct.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Like for fine activities, we have to show only forecasted values.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yes, sir.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Thank you.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "If you, if you look at that cash flow, indirect Excel, right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "It gives you the entire formulas of how to calculate your, your cash flow, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You just have to follow those formulas and what numbers it's linking to.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And you will get the numbers.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You will get what numbers you have to apply for a change versus what you just take as a forecast.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Numbers.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right, Just that Excel we've given.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You just need to follow it.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And it links through the different tabs of what numbers it's picking up and what accounts is picking up from.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You just have to follow that for one month.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So you understand and then you can apply that for the month.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Sure.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Ma'.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Am.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "So with us there was, with all.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That's the forecasting queries, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Were there any.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "These were all the forecasting queries.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So now given these queries, what's the latest timeline?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Simran for once you've built it and tested it internally with your QA before you hand over to us, what's your update timeline there?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "See, I can provide the updated timelines in some time so that we can discuss and then we can plan accordingly.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "That what.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "How much time it will require.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "And apart from this, we need to work upon the security points and the unit testing as well.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So I will accumulate the meeting with my internal team and then we can provide you with the timelines.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So for module two it is just a forecasted financials page which is pending.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "The other pages are done.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "You attached the other pages?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, See we.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "You can't check it out because the thing is that we have.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "We are updating the pusher to socket IO regarding which I need to discuss related everything with Ashbit.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "That's why I just want him to join the meeting because he just provided us with his feedback so we have some kind of queries on his feedback because these are some more of the enhancements instead of the changes because we have to put the extra efforts and that will even extend the deadline too.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So that was my only concern, that he should join the meeting so that we can have a discussion in the same call and then we can finalize everything.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay, I'm just messaging him so he can join.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Also I'm informing my two other team members who are working on a zero part and plus who are working on the socket IO so that they can discuss everything related to the feedback and whatever enhancements and architecture changes that Ashprit is asking for.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "The document that Ashpreet sent with the fee.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Any.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Any concerns you had on that.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We have documented we have two documents, one with his feedback and other one with the R responses to that feedback.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay, yeah, just bring it up.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Let's see if there's anything Gomy or I can maybe answer while he joins.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, sure.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yes, yes.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "As rhythm is not working on these.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "These kind of things.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So he can left the meeting for now because he's working more focused on the forecast module so he can continue his work.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Right?",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah, that's right.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Thank you everyone.",
                    "speaker_name": "Rhythm jalhotra"
                },
                {
                    "text": "Yeah, thank you so much.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Niha, please open the document they do with the ashpit feedback and plus that you have created the two of the documents.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "And firstly share your screen with the one with the ashp feedback.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So Bhavnit Neha is a front end developer and Manish the back end developer.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Hi bhavniti.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Is my screen visible?",
                    "speaker_name": "Neha"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "So I have gone through this third document and.",
                    "speaker_name": "Neha"
                },
                {
                    "text": "And we have implemented like a double Q system.",
                    "speaker_name": "Neha"
                },
                {
                    "text": "Now dashboard is saying that we should go with the Redis pub sub which will be a better approach.",
                    "speaker_name": "Neha"
                },
                {
                    "text": "And I have gone done some R D like Socket IO the W also a better approach.",
                    "speaker_name": "Neha"
                },
                {
                    "text": "Just the redis is like messaging queue like when the consumer completes the task.",
                    "speaker_name": "Neha"
                },
                {
                    "text": "Redis P also give the responses a little bit too fast as compared to the double Q.",
                    "speaker_name": "Neha"
                },
                {
                    "text": "So",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "WQ is also a better approach.",
                    "speaker_name": "Neha"
                },
                {
                    "text": "We just share the timeline as well.",
                    "speaker_name": "Neha"
                },
                {
                    "text": "That the recommendation which I provided by the split so will take our two working days off.",
                    "speaker_name": "Neha"
                },
                {
                    "text": "Okay so I think Ashprit has just sent me a message.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "He just stuck in a meeting.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Can we do 2:30 India time and in the meantime these your responses to his feedback.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If you just share it on the WhatsApp group he can look at it in the meantime and then Simran if you can just put in a call at 2:30 Indian time which is 1 o' clock UA time.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And then can join and then the full and then you and Aspreet and the full team can go through that and and come to a decision.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah sure it works for us.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "We can join it at 2:30.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "All right then I'm sharing the new meeting invite for 2:30pm IST.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah, yeah right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And apart from this we will try to provide you with the time estimations for the forecast module.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah and then the scenario modeling.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Do you how is that coming along module 3?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "See module 3 is totally focused and.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Because a lot of, because a lot of the calculations you're using in module 3 are derived from module 2 right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yes, yes these are all overlapped or interlinked.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So that's why if we have to work upon the few forecast financials in the forecast module and then we can only check with the scenario modeling and once it is done then only we can finalize both of the modules as these are interlinked.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So we will provide you with the time estimations of both the modules for now because scenario modeling is done but for now the socket IO regarding which we need to discuss discuss with Ashpreet and once it is finalized then we can provide you with that handover of scenario modeling.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "And was there anything on the AI plan that you wanted to discuss or that with Raheel and that's with Raheel",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "and Akash they were I believe they had discussion with Ashbay related to the second approach rack based approach for the AI module and we haven't get any feedback that with which approach we need to proceeded further.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So I believe they will provide us an insight on which approach we have to proceed it.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "If you have an idea then you can let me know because we are stuck in the AM audience.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "No, I think our approach is.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, go ahead.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Well I mean I recommend that we we still need a little bit of a discussion on our side and then we'll get back to you asap.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay, no problem.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Then you can have your discussion and then you can let us know Still I want to highlight it here that when one you inform us that with each approach we will need to proceed it further.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "According to that, I'll provide you with the timeline for the AI module.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So it all if any kind of changes in the architecture or whenever we get the clarifications just now, we have get clarification the forecast module.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So we will work on the forecast financials.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So according to that the deadlines would be changed.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "That's why I'm just informing you just an insight for you to that once we get an approval on the approach for the AI module, then only we will start working on it.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay, that's noted.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That's fine.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "All right.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So let's connect it to 30 then.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "All right, thanks.",
                    "speaker_name": "Ngũmi Gituro"
                },
                {
                    "text": "Okay, thank you.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Bye.",
                    "speaker_name": "Ngũmi Gituro"
                }
            ],
            "summary": {
                "overview": "- **Forecasting Formulas Clarified:** Team aligned on key forecasting sources for cash flow and balance sheet to reduce confusion.\n\n- **Investment Data Usage Confirmed:** ONCA will use 2025 forecasted numbers as placeholders for goodwill and investment property, simplifying calculations.\n\n- **Module Development Progress:** Only the forecasted financials page remains incomplete; timelines will be reviewed post internal QA.\n\n- **AI Module on Hold:** Development awaits strategic decisions on approach and architecture, impacting resource allocation and timelines.\n\n- **Improved Communication Practices:** Direct discussions with stakeholders enhance decision-making speed and transparency, reducing previous delays.",
                "action_items": "\n**Project Manager SFS**\nProvide updated delivery timelines for forecast module after internal QA, security, and unit testing (39:02)\nShare Ashpreet’s architectural feedback documents and coordinate team to address Socket.IO implementation and feedback (40:20)\nOrganize follow-up meeting at 14:30 IST to discuss architectural feedback and finalize decisions with Ashpreet and team (44:40)\nProvide timeline estimations for both forecast and scenario modeling modules once Socket.IO discussion is resolved (45:06)\n\n**Bhavneet Mhajan**\nProvide missing forecast formulas for ONCA items and clarify formulas during the call (01:29)\nDocument and clarify classification codes used in cash flow forecasting formulas to ensure alignment with database fields (07:55)\nConfirm exclusion of accumulated depreciation from UI and balance sheet output (21:04)\nExplain financing activities cash flow breakdown and formula components clearly to team (24:01)\nGuide team to use forecast actual values in UI and variance column to show monthly changes (33:54)\nConfirm that forecast numbers for ONCA items can use prior year’s data as base (23:15)\nHighlight to team to follow existing indirect cash flow Excel workbook formulas for correct cash flow forecast calculations (37:57)\n\n**Rhythm Jalhotra**\nValidate and provide actual sub-account values for prepaid expenses and link to OCA changes (01:54)\nProvide clarity on codes used for change in earnings not attributed to retained income and forecast components (04:48)\nConfirm removal or resolution of “CE” code ambiguity and database mappings (10:05)\nConfirm fixed assets formula use with property and equipment only and accumulated depreciation exclusion (20:18)\nShare screenshots and data to clarify forecast vs. changes for short and long-term debts and other financing activities components (30:02)\n\n**Ngũmi Gituro**\nRecommend showing forecasted values in cash flow with variance column for changes to aid clarity (34:33)\nSuggest tracing database extracts for example months to clarify source of forecast inputs (14:38)\n\n**Neha**\nPresent analysis of Redis pub/sub versus double queue system for messaging; estimate two days to implement recommended Redis approach (42:40)\n",
                "keywords": [
                    "forecasting",
                    "cash flow",
                    "ONCA",
                    "financing activities",
                    "database codes",
                    "Socket.IO"
                ]
            }
        },
        {
            "id": "01KMHQSBYB1RAGY2X4EP6DCMC9",
            "title": "Nolocode AI meeting",
            "sentences": [
                {
                    "text": "It.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So I think everyone's joining in about five to ten minutes.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Probably less.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "But yeah, if anyone wants to get tea, coffee or anything before we start then have some time so feel free to do so.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "No, no, we are good to go.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "If you want to have that then you can.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah sure.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "I think I need it.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Then you can have it.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Your voice saying that you need it.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Thank you.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "I'll be back.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Five minutes.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Sure.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Good morning everyone.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Very good morning, how are you?",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "We are just waiting for Ashpirit to join and then we can key off the meeting.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So do we have Raheel and a.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yes, Akash is available and he will join in around five minutes.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Hi guys.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Morning.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Good morning.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah I'm doing great.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Who are we waiting for now?",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "We are waiting for Ashpree.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Once he joins then we can start with the meeting.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "All right.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Hi Badnet, do you want to check with Ashpeed when is he joining?",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah, just give him a couple of minutes.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, thank you.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Hi guys.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, hi, how are you?",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay so I think we have everyone now, right?",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay so if we can then begin with first like do you have direct questions Ashby Bhavni or should we give you an overview of the first approach and then the second one and we can help you compare and contrast between them.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah, we can quickly like summarize the two approaches or what is the proposed approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay so yeah Simran is harsh going to take the lead here or.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah sure can take the lead and he can confirm everything related to the first approach and the second approach.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay so hello everyone.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So I'm sharing my screen and then I will explain the both approaches.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Is my screen visible to everyone?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yes, it's visible.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay so like I will explain using this diagram.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So we in our chatbot we have multiple types of queries.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So some queries are related to like what today the data which is present in database like revenue and other things.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Some queries are regarding the like the applications and.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And what are the formulas using.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Some queries are regarding the stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So depending on these types of query we handled these things differently in our flow.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So in.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "In this is the previous approach which I am showing to you.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So in the previous approach when whenever the user query was coming to the chatbot the chat was classifying the user query into a stress test query like this query.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "We need to perform stress test on this query or this query belong to other things like regarding the database and general query.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So if it is stress test query then it is go it was going to into different flow.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like there was a separate flow for the stress test which, which I will explain now.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then if it is not a stress test query then it was going in a different like it will get the data from database and answer on that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So now let me explain how the stress test being implemented in the previous approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So here it is explained.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah, so in the previous approach we were getting a concise explanation of about the stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "What is the stress test is about what are the input providing.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "The stress is explained here for example in the recession playbook is a stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So we will, we were getting like what will be the input required to execute this test test?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "What are the reasoning which need to be performed to get out from these tests and what are the output format we need to to show in the output what are the graphs and the summary and other things.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So we in the like before like including stress test we will, we will be needing our document in the previous approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So our document should contain again inputs business logic and failure condition and expected output with an example.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So after we get these things regarding the stress test then we were like understanding the logic and coding it into the repository in the repo in a different folder.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So for every stress test we were creating a separate Python file which includes the logic we need to be implemented for that stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So we were identifying what are the inputs regard need to execute the stress and we we were writing queries to get this input from the database.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then we were implementing the logic for this test test and so, and then implementing it.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So after the whole like logic is implemented, another extra step needed to this that add the that stress test into the query classification prompt.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So as I already told you in the first step we were classifying the user query according to stresses.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So if we have five stress tests then we will be needing like five types of stress test in the classification.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So for every stress test a new classification need to be added in that query classification prompt before after writing its logic.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So in the previous approach first we need a document.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then by understanding document we were creating a Python file implementing all the logic from the document.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then we will we were adding a classification regarding that stress test and then we were writing unit test cases and verifying it.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then yeah, that's how we were integrating the stress test into the chat flow previously.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So like in the final step the chat like after the classification, after the query is classified that this query is need to be executed into the using stress test, then it will be routed to that Python function which will which we have created regarding the stress and the response will be come from that function and will be shown to the user.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Now let me show you a demo of this implementation.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "This is the previous approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Just go down.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "I wanted to see the pros and cons you had below the document of the previous approach.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Can we just go through that before?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So I think it will be better if I explain both approaches first, then we can go through this.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah, or I can go just for approach one.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So like for approach one, like it is, it will obviously be faster because all the logic is already implemented and and queries are already written for that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So it will be very much fast and token usage will be less because already logic is written and it will not be retrieved from Vector store.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And since if, if I stress this include a very complex logic, then it will be handled properly because a developer will be handling all the test cases here.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "The only cons for this approach is like it's required to for every new new test to be included, it required to add a new Python file in the repository and then again deploy the code and then test it.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So that, that is the cons here.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And these are the force for the approach 1.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So in your view, harsh.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If you were to, if you were",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "to create a new a sixth preset question that would require a new code, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "How long would that take in your estimate for developer to do that?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, create another five preset questions.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So I have five of them and I want to create another five to get to 10.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, so we have implemented the recession Playbook stress test and it took around like three days to implement it properly.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So like it was actually complex too.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So if I stress test is easy to implement, it will take around like two days, but generally it is taking three days to implement a new stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So three days per preset question.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So five.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Then that's 15 days.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "15 working days.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yes, you can see.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Let's have a look at the demo.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, So this is the chatbot.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "I am asking the question here.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Let me refresh.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "It.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay, see this time response is written in 31 seconds.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So the response is, the question was if the market dips and we miss revenue by 20% from quarter three, what do we need to cut or delete to survive next four months?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So it analyzed the current situation and provided the mitigation plan along with that, all the scenario like shown in the graph as well.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And after that recommendation and assumption for this stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So this is the previous like approach on implementation of recession playbook Stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I just want to read each of the four points one by one.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "First like without mitigation the company starting cash balance of AED is this and below target is minimum cash flow of aed.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "The company fails to meet its survival target from month one under the recession scenario.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Second is mitigation plan.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "The recommended mitigation enrolls are 20% reduction in operating expenses and a 50% reduction in capital expenditure.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "This plan increase the minimum cash balance to AED this and successfully exceeding the requirement floor ensuring survival.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Also the graph includes the base scenario and the minimum cash flow which is used here to compare and with with mitigation.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "What will be the effect after mitigation?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So graph is showing this and then there there are recommendations like secure immediate short term liquidity through credit lines or equity to bridge the initial cash shortfall and meet the minimum floor.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Conduct a comprehensive cost structure to review and identify additional efficiency opportunity beyond the current mitigation.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And the third one and after that the assumption which are used in this.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So the this analysis assumes a minus 20 revenue drop starting month 1 unchanged COGS, percentage stable working capital timing and no changes to the tax or external funding.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Where we got the minimum cash flow balance from?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Sorry, can you repeat the question?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Where have you got the minimum cash flow balance?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I said the minimum cash cash flow balance was 2.2 million.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Where have you got that number from?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I think we are using a formula for this.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Let me confirm.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Minimum cash flow.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah, minimum care.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "For calculating minimum cash flow we are using one rate into the Runway months.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So these value are present in the db.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So using that we are calculating minimum cash flow.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Any other question and how does that",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "number compare to the current cash balance?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Cash balance was half of that.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Current cash balance 1 second.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "You are.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, I have to look into into it.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "The whole data is coming from the db.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So the number are directly like this logic is getting number directly from dv.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So for that I have to look into the.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "As in my question is if the actual cash balance is half of that how do we have a minimum cash flow as double if the existing cash balance is the same.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And the question is we want to survive the next 12 months so we have the existing cash balance.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "How can we have a cash floor which is double up on a forecasted cash out cash balances.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay,",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "and just when you go up, if you look at the mix it says 20 reduction in opex and 50 reduction capex.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "What were the different mixes?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right, it's come within.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, it's Come with the recommended mitigation of 20 in Opex and 50 it must have come up with various different combinations, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "What were the different combinations and how did it arrive to that 20 and 50.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, so currently we are not storing that all the com on like combination which are returned by the logic.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "But the arrival to the final combination is based on the pen score logic we have implemented.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So we are assigning every like scenario combination of pain score.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So based on that it is like getting to the final conclusion.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Is it applying a criteria?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "How is it coming to a conclusion to say the best option is a 20 reduction in optics.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, I think we have a document regarding this.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Let me show you.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Oh, I can see the logic directly here.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Give me a second.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Document.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "This one?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah,",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So we are using this logic to get to the like the best combination out of the like survive scenarios.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So OPEX for OPEX we are assigning this pin score for capex this and then we are like calculating pin score for every survive scenario and picking the best one out of that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay, let's go to the Unless if Ashpreet or Gomi have any other questions, I think I'm okay to go to the second approach.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, let's go.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So the problem with the first approach was it for every stress test we need to implement it manually and change in the repo and then need to make it live again.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So that was the major issue.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "For that we start searching for a scalable solution which is in which",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "it",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "is easy to add another stress test and can be integrated in the flow automatically.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So for that we came up with this approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "It is a two step process.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So in the first step the document is still required.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So I will directly explain it how the new test case will be inserted in this approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay, implementation strategy.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay, so in this approach first initial requirement is still the same.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "A document will be required with all the necessary input.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "After that document will be processed into the markdown format by an agent.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Previously, what the developer is like processing document in the python file.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Now this work will be done by an agent in a pipeline.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So document processing step will be done by agent and it will generate a python function regarding that stress test and then the agent is run will run that stress test within a provided example by referring to the initial document provided by the financial expert and then validate the file generated function.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then if the function is validated, then the that function is indexed into the vector store and will be available to the answer generating agent.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And if if the like the generated function is not Validated then it will be flagged for correction.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So I will explain this via flow diagram.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Now give me a second.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So yeah, so the first step of this flow is like storing document in the vector vector database.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So I have already explained this a document is needed Agent will process the document summarize and create a python python file for that or a python function.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then if the then execute that function on the user provided example.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "If the out if the output is correct then it will index that function along with the summary.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And if it is incorrect then flag the document for manual verification.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So this is first step of the second approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then how it will be integrated when agent is generating the answer.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So here user query will be analyzed like user query.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Based on the user query relevant document will be fetched from the vector database.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So then agent will will look like compare the user query with the relevant document.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So so if the user user query is about stress test and like the input required for the stress test also available in the query then it will go ahead and like start executing the stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Else it will like answer the query based on the retrieval document.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like it it could be about the application on the formula or other things.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So now if the query is about stress test agent will gather all the input required to execute stress test test using a query to SQL tool.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "It will fetch all the data from the database and then execute the stress test using that function which is which we previously stored in the vector database.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then the result generated from that function will be like shown to the user like yeah, this will be like updated flow.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So here we will be needing two agents.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "One for indexing the document and the second agent will be updated for this like for analyzing and like for executing the stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So x second, there one more thing in the second approach which I need to mention 1 second.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Picture.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So in the like while when we start when we will implement the second approach, first we will go with the single agent approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like if the single agent is enough to implement the stress test on his own, then we will like stay with the single agent.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Else we will again like move to a multi agent architecture in the answer generation pipeline.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So there will be a primary agent which act as a supervisor agent which handle the query.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "If if the query is general or delegate the query it's regarding the stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And then specialized agent will be made for executing a stress test only.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So this is the second approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Is there a third agent who does a validation of the simulation analysis.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So the second region does it as a preparer as a reviewer who also reviews the output and validates it.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Okay, so the primary agent provides secondary agent the function of the stress test simulation.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then the second agent is responsible for get gathering the data, validating the data and generating the output and validating the same.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah,",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So the second reaction is validating the work is prepared is what you're saying.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, simulation result will be validated by the second agent.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like yeah, if we move to like multi agent architecture.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "If the single agent is enough like if we get good accuracy with single agent then we will stay with the single agent architecture as we are already doing.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So like should I show a demo of this approach or you have any question regarding the like how it is being implemented?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "We can show the demo first, then we can take up the questions.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So like this is a.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "This is Langsmith platform for like testing the agent rapidly.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So I built the POC regarding the approach to.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So I will be showing you a demo of that POC using this platform.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So I'm.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "I will stay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "I will be again executing this stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Queries.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So this is the query if the market divs and we miss the revenue and this is the company ID and user ID for that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "We'll be automating that when we move to production.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "For now we are providing it in the query.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So agent will hit the query.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So first it retrieved the document from the vector database and retrieve the function to execute the stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Now it will go ahead and start gathering the data required to execute that stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "It passed opening cash balance and one rate it is getting monthly revenue OPEX and capex.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah, forecasted data is here now.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Revenue for.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay, So when all the input are fetched from the database then it it use and tool prepared to execute the stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So that tool required the simulation function for stress test and the input which is gathered from the database then execute them on the stress test then return the output.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So as of now I think there's a.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "There's an issue in the function that's why is returning insolvent.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "But yeah means it can be executed in this way also.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So when inputs are gathered it will be passed on to the function dynamically and the output generated by function will be returned and it will be shown to the user in proper way as we are showing here like in the form of graph and the summarization and other things.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So for now it returning this with the four months.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Under this condition your cash balance will fall below the minimum required cash of this within next moment.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "This means under these condition your cash variant Will fall below the minimum distance.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So the purpose of this POC was like examining that we can execute the stress test dynamically or not.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So it is possible like after doing the poc.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Harsh.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Is there any like.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Is there proper output?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Have you ever.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "If there is improper output of previously which you have run, can you showcase that?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "I need to look into that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Did I have that?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So what I believe you said in the previous approach there will be unit test cases.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "All of that will be part of pipeline and that requires more effort in terms of validating and it.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "It has a deterministic output.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Based on your initial testing, what I would say what.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What made you feel that this is a better approach in terms of solving a same problem?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "In terms.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "In terms of solving what?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "See same situation.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "You felt that this is a.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "This is an agentic approach.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "But it.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What extra you get with this approach?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Right?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "That's.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's documenting.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So parsing from document is one, what's another?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, so previously defining a deterministic flow in code that's one piece you need to do it from a markdown document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's one difference.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What I feel in a functional building up what others.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, so another could be just helping you out.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Another could be.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "This is a multi agent flow and that's a single agent managing everything.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So what all think you feel?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "The other thing here which is changed is we are like getting stress test function from the vector database.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So we were like previously we were routing it into our code, but now we are getting that from the vector database and we are executing it into the flow itself.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "That needs to be part of vector or is just.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "This can just be part of your lang graph node and subgraphs also you can manage that from subgraphs also your deterministic flow.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Right,",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "we can manage that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "But again for classification we need like.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "We need what?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So how we will classify the query then?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like can I.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Can I.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Since you have filled in, can I look into a document which you prompted as a. I would say for embedding into a chunk date and then you push into PG vector.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What is the document?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Are you looking at?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, which document?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "You are like here the status quo document which you fed into the vector db.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Okay, one second.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "You are talking about the flow.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Your first step is you have a set of documents which have let's say a set of stress tests.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I want to look at what.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What was the first step?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Which document?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "How the document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Let's say it was on docx.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I will want to look into the docx Document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, okay, So give me a second.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "This is just like sample we referred to while creating the function for the four vector database.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So you got this document from like",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "we created this document on our own.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay, yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Then after that like we just give this document to the to LLM and that just created strategy.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So what is the stocking strategy?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What is chunking strategy?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "How did you bifurcated this logic?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Oh no, yeah, that part is for like first agent which.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Which will like convert documented to markdown and like write the function for it.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "For the POC purpose we just like give this document to the LLM and created a concise function which is including all the logic just for like like looking like feasibility purpose.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like if it is possible not.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "But yeah, we can also convert it using agent as well.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "My point here is we didn't like write the agent to convert this document in the Python function for now we just created a sample function for that that is not done yet.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Just a point.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Ashby, this was on the motivation of you said that you wanted.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "I do understand.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "But you want to understand.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "See, see for me the document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So if that this document is going to be part of my general let's say flow I need to understand what is the document about.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "How they have chunked so they have reached to a success story around it.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "See, that's important because.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Because I need to follow the same strategy of building a document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's the simple garbage in, garbage out.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "If there is something that Harsh will identify will give you a template that we think that works.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Happen based on",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "processes.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "For now you just give this document to lm.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, that was just",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "so like I have already implemented recession Playbook.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "This would give you a better output than the deterministic one.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Actually output will will be same because we will be validating it before like indexing that function into the vector database so the output will be the same like in both cases.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And I think Harsh has concluded that the output both from either approaches was the same.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "It's just a convenience in the document ingestion phase that you get here.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "I could see There was a 30 seconds latency in the previous one.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Any.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Any add on to this approach or it will reduce that thought.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What is in in general without using any caching or any other reducing latency technique.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What is the Apple to Apple comparison in between both of them?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So like for the second approach currently it is taking around 60 seconds in POC.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So it is almost double like.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And token utilization would also be double in the Agent, right?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, right.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "It is.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah it almost earlier.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "I have also written",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "optimization or once you've optimized the flows beyond poc, what would.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "What would you expect?",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "A realistic.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "I can like after optimization latency will definitely be decreased but how much it will decrease that will depend like 10 second delay can be easily done like around 50 seconds it can be like executed but after 50 seconds like we need to see like based on the optimizations and the token utilization will also be less like we can also include like cheaper models for like steps which don't need so much intelligence.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Which model you were using as of now for POC?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "For both of them?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Gemini 2.5 flash.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "It's a fast model.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, it's a fast model.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So you don't need any.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I don't think so you need any thinking model even for multi agent also.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, but like I experimented with Gemin Gemini 2.5 flashlight.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So for with that responses were fast but they were not that much accurate.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So a little bit of experimentation needed here.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "But in terms of.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "When you say it was not accurate what that's.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Can you be bit specific?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "It was not giving right numbers.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "It was not able to summarize better",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "so it was not able to like form the SQL queries properly rest it was doing good but in case of SQL query formation it was not good.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And by the way did you get a chance where I have suggested flow four agents in the multi agent.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Did you get a chance to look into it?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So I. I don't remember like when did you suggest it?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "No worries, no worries.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I have.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I'm just sharing a document here Again I've also commented you so I believe that will add more.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "More complexity and will need more.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay, let me.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, you are presenting.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "No, no, I'm just shared the document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I am it's just that validation one which also said.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "And second I'm saying one two just pull in the data it's it so one supervisor who understands the routes based on intent and requirement.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, just four of the things anyways you can look into it.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "For the question we can do one thing.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We can share you like for the session playbook only we can share you everything in detail.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like how we are getting the values and what are the like different possibilities where like agent is looking into and what is like then a response that is returning.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So you can also look into it how we are calculating and you can check all the steps in detail and if you find anything concerning you can let us know.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Have you Planned out how your let's say I've given you four agents plan planner out how you will work with sub graphs and graphs and nodes and tools in each agents based on their role.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "And yeah you try to create a lang graph and identify how will you solve it.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "And let's.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Let's come back on the design then.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So Ashpreet, you.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "You'd want to see that design before you make a decision, right?",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah because what I feel I'm still not confident with the output received in the deterministic flow approach one that's.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's what he feels it's.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Maybe it might require more testing or",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "more",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "I would say validation.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "All of that.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah but if we need to go into the approach to then we have",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "to be pretty",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "solid in our design.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So when we start implementing it should solve it because based on the document if document is not well articulated or given to the vector I embedded correctly it will still have the same issue of and getting into it.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I just want to solve that problem as well.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "If you're going to that approach.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "If we are going to that approach.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "How better refined because let's say he says three days of effort in.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "In this deterministic can we into one effort adding another another stress test with this current approach.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "If that saves me time and effort and make that production ready in within one day.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's the benefit.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I get it with the new approach and I can take a better decision.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I hope that sounds well to you Akash.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "It makes sense.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So if I could suggest that we the comparison pros and cons part that you had in the document if you can expand that out to include more detail around once you've optimized what we can achieve on both approaches in terms of setting up a new stress test latencies included the tokenization and all the details that will help them.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "If there's anything else I should be up missing let me know.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "But if we can summarize that one place that I think would be useful as well.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "All right.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "And sorry one more thing.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "There are some feedbacks on Unified Document and have some feedbacks in this document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I just want if you can combine that or put everything on one page so it helps for module four.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Akash,",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "so you've sent some stuff to us and you want it consolidated in that unified scope.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah, so I have.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "I've given feedback to both of the pages.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So there was some bit of information on Unifieds and some of bit of this new AI architecture one so you can Just correlate and put it together.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That helps you as a feedback also so you can work on just, just whatever sounds better to you so you don't miss any feedback.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Just that.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, so Simran, let us know if you guys have access to the documents first and then if you could do it and then give us your feedback and then we can decide how we want to combine it onto the document.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Sure.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "I'll check the assess and then we will look into it that the feedback that he provided on both of the features and then we can consolidate that and can work accordingly and then we can start with the design part that he requested for.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay, thank you.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "I know it's hard to predict how long this activity and preparation will take, but roughly are you guys in a position to suggest now or would you need, you know, you can take some time after this call to let us know.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "We need some time to look into it and then we can provide you with the estimated time that how this effort will require Time.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah, sure.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "If you could let us know so we can let Katie team know.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah, I'll ping you.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So regarding the efforts or regarding how much time that we require to do all these things and when we can showcase you something",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "I have, I have some question to Ashweet.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So when you were asking about chunking so you are asking like how we are storing it into the vector database or how we we are converting the document into the function.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like I, I didn't get it storing into vector database.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So you, so let's say you cannot chunk the complete document into one or, or you can identify.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, this is the fun vector.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "How do you want to solve it?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Because it's a, it's a problem then has a solution.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "But it's a, but solution is a big document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What I see it's a two page document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay so like I can answer this question like so yes I can.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So, so, so the, the document.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So the second approach, in the second approach the agent will generate a concise summary of the whole document and a Python function which like contain the simulation logic and provide output.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So what we are doing here is we are generating embeddings of the summary which was provided regarding that stress test.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And so when the query will come the similarity search will be like based on the summary and the output which will be given after that search is the executable function.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So it's a kind of parent document retriever.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So we will apply search on the summary and the output will be the stress test function.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So we are not like embedding the whole document or this.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "We are just embedding the summary of the document like this much only.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "And what is the retrieval strategy?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "It is.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Since I can see you have added metadata.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So you.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "You're providing as a metadata.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "How do you searching from.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "From the vector.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So we are searching based on query and.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And the output is metadata.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like in the output we are getting the three field from the metadata.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "That is entry point and the function which is need to be executed.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "It's just a semantic search.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, it's a semantic search.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Okay, so I will suggest you since you have a metadata also I will suggest you use a semantic search kind of in a hybrid search semantic plus and metadata.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Because you're using metadata also attack.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So that will fast your help you to your query will be faster and more try that approach.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, I I will look into that also.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like if it makes it more accurate and fast, then we will surely do that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "We can do that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah, because you are already.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Because during your chunking you're storing as a metadata as well and summary as well.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Because okay, so during your retrieval you if you do this it will faster query will be faster.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, I will look into that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Oh and and the second question is the document you provided where four agent are mentioned.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So regarding that you are saying that go through that document and like what's",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "your thought around that?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So like and then come up with like optimized approach.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like it's a optimized version of the approach too.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Am I correct here?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So you are asking like how will we can implement it?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Like how much time it will take and all other things regarding that.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yes, yes.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "And other than that like you want the like feedback on.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "On your points which are like the feedback which you gave us.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like we need to.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We need to give a thinking on that too.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Back on my point.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I'm just looking take that in your account and think how you design it.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Actually we have replied to some of your queries yesterday.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "If you have like if you want like we can do it now.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Otherwise we can take up it like next time.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If you have any.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I could see he said we are already it's in high level one.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "We have taken care of the feedbacks.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's fine.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's fine.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I understand.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "If you've already taken care, that's good.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "If not take care.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's one in approach to.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Maybe their feedback is not missed on is missing because that was in a different unified scope document your feedbacks are 1 on AI Architecture Diagram 1.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's right.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "I have defined agents definitions there because previous year also mentioned previous ones there.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Just look into that input document.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, sure.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "And we need to provide with the design as well.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I'm saying think about how you better design it.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So it helped me as an user or also as a client.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Let's say if you're.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "If three days has been taken can we optimize do a one day production ready deployment.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's what I will say.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "If effort right.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "That's when then I will be able to take a better decision also got your point.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "So on the whole you need an optimized version of approach two.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "But three days like we said for the approach one.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We didn't set for three days for the approach two.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "I do understand.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "I do understand.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So let's say.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Let's say if you say approach to is already optimized and solved it from one day itself.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Then it's good for me.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Actually Ashpreet like suppose once we goes with the approach too.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So like only thing on your side is to do like.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Is to like we'll share you a template of our document.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like how you doing to define this test case?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "You just need to upload somewhere like we'll provide you a UI over there.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "You just need to upload it.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Rest of the things like, like.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like we like it's just will be done in the matter of time only like once you uploaded it like at the back end it will be stored like it will generate a summary and a metadata.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Then it will be stored to the vector DB and then you can run a stress test case over it.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Like it will not require so much of time.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "It will just run in 5, 10 minutes only.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah agreed.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Agreed.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So based on what input I have given you based on 4 think about that perspective.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, yeah we'll.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We'll give it think about that too.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Just I was clarifying like in the approach to will not require a day also like it will be done in five, 10 minutes only.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah, that's what I'm expecting also.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah, yeah thank you for that clarification.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yeah thank you.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We can.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We are good for normal.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "No, I was just going to say so thanks for the discussion.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "We'll consolidate everything and if we can get a accurate comparison between the two so we can share as we said that'd be great.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Nothing else from my side.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "So I'm not sure Bhavni and Gumi anything else you want to raise on top of Ashpree mentioned.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Or anyone else on the call.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Any other question?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yes, sorry, go ahead.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "So I want to clarify one thing so the optimized approach Waspreet said basically that's fine but these are just.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I just want to clarify from the call earlier with Raheel that Raheel also mentioned these were for the preset questions.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "So for the normal questions there's no discussion there.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "It's a RAG based approach for the non preset questions I just want that clarified this call.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Sorry, when you say preset.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah, go ahead.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "S so for normal question if they are regarding the like the company or like the document stored in the vector database then they will be answered using the regret using the reg and if they are regarding the like formulas yeah value stored in the document for example what is the revenue of January to 26?",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So then they will be answered using the data present in the SQL database Else if the question is very general like it's a greeting or something then they will be answered directly.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Let's say if there's any question on clarification some definitions and that's not part of let's say their learning parameters of the LLM and I have given is an FNQ format in the rag let's say just some definitions would that be able to answer without any retrieval from database?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "No.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Like if it is not the part of like LLM training then it there are two possibility it will hallucinate or like it will not answer.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "So in that case like we have included in the prompt if you don't know the clear answer then I gracefully decline it or only answer if the you have the supportive documents in the vector database.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Let's say it just asks what is Achilles?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay,",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "you will not know Kleids right?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What will the answer hallucinate?",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "What I believe",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "so like in this case it will say like I don't know like about Achilles can you like I I am not able to answer this question or something like we will show a default message or like we will suggest a question like pull up question or something like that but if the document is present in the vector database or you have loaded some FAQs or something like that it will answer",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "using them only so we expecting that to happen.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "So if we have uploaded if in Q it should answer yeah so that's the expectation.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Let's say we add that okay should answer so we need that flow okay",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "we'll integrate that for you we'll indicate some basic effort so it'll be an",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "extra current of the flow plus what Harsh mentioned would be the values.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "So if you.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "If a user wants to ask what was my revenue in January 2023 they should able to answer that as well.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "The types of questions would be FPA FAQ related questions or questions about their historical performance.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Or also questions about the module two and module three that you've created.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So it might ask you what was my what did I Forecast for revenue May 2026.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Right.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "So this rag based approach should answer all these types of questions.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "We have all that included, right?",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That's right.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We will.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We have.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We have done that.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Some part of that also.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "But yep, it will be covered.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yep.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Yes.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Just.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Just the basic Q and A just which you have mentioned.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Right now we just need to include that part only.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Other than that like all of the things for the past data which we have, anything forecasted which we have it will be answered by the anything you asked questions related to that.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So Karen, just to.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Just to clarify a bit further question that that would be possible for both approaches, is that right?",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Actually that approach one and two is just for the stress test case.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "It's nothing to do with the simple Chatbot A.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yep.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "It will be done in both if you simple.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "If you want a simple answer, it will be done in both.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "I think the approach one or two is just for the preset question.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That's right.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "That's right.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "That's right.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "We we will be giving.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "You'll be using a ragbage approach because you're asking questions and giving all the information whether it's finance terms, FAQs, historical data calculations or you know, forecasted calculations that the model has all that.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "And like the previous question when Harsh was showcasing you like how the, like you were saying like it was showing the double the value or the half the value of the.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "But what was the cash flow like asking the question like how is the cash flow value showing like showcasing like this.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So do you want us to like create a document especially like highlighting like what are the values we get from firstly from the DB and what are the possibilities?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "It is gathering, the AI is gathering and then after that like how it is picking one of the possibilities.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Do you want any, any of that?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yes, that would be.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "That would be helpful to see what it's.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Then we'll share it by today or most of the tomorrow and you can.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "You can go go through that and you can let us know if you.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "If you have any concerns over over our approach.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "And we also highlight what are the formulas which you use to get the different values.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So do you can have a more clarity over like and, and like the possibilities which I'm talking about?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "There are a lot of possibilities like, which the AI considers but we'll highlight like five to 10 possibilities like, like, but how it is getting that possibilities will highlight some of the like main things to you.",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "So do you can get an idea about that and you can let us know if you have anything about any, any concerns?",
                    "speaker_name": "Karan Middha U0438EU2CSX"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Thank you.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Anything else from anyone on the call before we close?",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Bhavneet Mhajan"
                },
                {
                    "text": "Or nothing from a site.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Please feel free to message me anytime on WhatsApp if there is any immediate support required.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Okay, sure, sure.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "We will continue.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Perfect.",
                    "speaker_name": "Ashpreet Singh"
                },
                {
                    "text": "Thank you.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "So if there's nothing else from anyone then I guess we can close the call.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "We've got some actions get you back some information to review.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Hopefully the next couple of days will confirm how long that will take after the call and yeah, we can, we can pick it up from then.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Sure.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "We will provide you with the requested documents and plus whatever we have suggested and then you can finalize according to that.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Thank you, Samra.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "All right, if there's nothing else, then we can close the call for now.",
                    "speaker_name": "Nolocode AI"
                },
                {
                    "text": "Yeah.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Thank you so much.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Thank you for time everyone.",
                    "speaker_name": "Project Manager SFS"
                },
                {
                    "text": "Thank you, Tim.",
                    "speaker_name": "Harsh Vardhan Dixit"
                },
                {
                    "text": "Thank you.",
                    "speaker_name": "Ashpreet Singh"
                }
            ],
            "summary": "null"
          }
            
        ]
    }
}
