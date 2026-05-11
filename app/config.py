import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FIREFLIES_API_URL = "https://api.fireflies.ai/graphql"
    API_KEY = os.getenv("FIREFLIES_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"

# Development constant transcript for testing
# CONSTANT_TRANSCRIPT = {
#     "data": {
#         "transcript": {
#             "id": "01KQF1G1MWVNM7AKDNHVAS0Z38",
#             "title": "fireflies automation testing",
#             "sentences": [
#                 {
#                     "text": "Hello Hello.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "My testing my texting 1, 2, 3, 4.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "So in that we are discussing stress test.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "No, our.",
#                     "speaker_name": "Harsh Vardhan Dixit"
#                 },
#                 {
#                     "text": "Studies working on.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Shut the.",
#                     "speaker_name": "Harsh Vardhan Dixit"
#                 },
#                 {
#                     "text": "Hell up.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Shut up.",
#                     "speaker_name": "Harsh Vardhan Dixit"
#                 },
#                 {
#                     "text": "Don't shut up.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "There is a lot of things happening so we don't have to shut up.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Now you.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Now it is ready for testing.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "We have to give 23 minutes more.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Now I have to go to reset Hazik.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Sa.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "La.",
#                     "speaker_name": "Harsh Vardhan Dixit"
#                 },
#                 {
#                     "text": "There is nothing holding me back.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Now we are speaking Trying to speak the song a lot of songs in my head.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Now we are moving back first two nothing holding me back so now let's start.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Wish.",
#                     "speaker_name": "Harsh Vardhan Dixit"
#                 },
#                 {
#                     "text": "Let's do one thing.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "We have to go back and see what we are doing.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Now there is nothing holding me back so we have to go you all right?",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Now we are all right.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Let's search for something that we don't do Right now we have to create our API backend API Then we have to integrate with Ngrok.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Ngrok is working fine.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Now we have to move to fireplace webhook fireplace Webhook is also doing correct.",
#                     "speaker_name": "Sahil Aggarwal"
#                 },
#                 {
#                     "text": "Now we have to.",
#                     "speaker_name": "Harsh Vardhan Dixit"
#                 }
#             ],
#             "summary": {
#                 "overview": "- **Stress test readiness confirmed with 23-minute countdown**; environment set for live stress tests, no current blockers.  \n- **API backend development underway with Ngrok and fireplace webhook integration**; critical for ensuring smooth data flow during testing.  \n- **Ngrok stable for backend API exposure**, allowing secure access; essential for comprehensive integration testing with external systems.  \n- **Fireplace webhook operational**, facilitating real-time communication and event handling for enhanced system responsiveness.  \n- **Immediate priority on backend API creation and integration**; pivotal for validating connectivity and data handling in tests.  \n- **Team to review current workflow and testing scope** to prevent overlooked issues and align on next goals.",
#                 "action_items": "\n**Sahil Aggarwal**\nAllocate and manage the 23-minute testing period for stress tests to ensure thorough evaluation of the system's performance under load (00:49)\nReview previous development work to identify any gaps or incomplete tasks to ensure all components are ready for the next phases (07:21)\nDevelop the backend API as the next technical step to support project functionalities (07:21)\nEnsure the backend API integration with Ngrok remains functional to facilitate secure tunnelling and testing (07:21)\nProceed with work on the Fireflies webhook, monitoring its correct operation to maintain system communication and data flow (08:16)\n",
#                 "keywords": [
#                     "stress test",
#                     "backend API",
#                     "Ngrok integration",
#                     "Fireflies webhook",
#                     "testing readiness",
#                     "development review"
#                 ]
#             }
#         }
#     }
# }


# Production level Transcript
CONSTANT_TRANSCRIPT = {
    "data": {
        "transcript": {
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
        }
    }
}
