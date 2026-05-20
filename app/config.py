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
              "dateString": "2026-03-19T06:44:26.000Z",
              "sentences": [
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Would have been great to like also have gotten these questions before yesterday and had you guys already shared this document with, with what's the name Akash or.",
                    "start_time": 0.08,
                    "end_time": 12.4
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "No, we have to share any kind of document with Akash yet because they just informed us that we can discuss everything with you.",
                    "start_time": 14.96,
                    "end_time": 21.36
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So that.",
                    "start_time": 21.36,
                    "end_time": 21.84
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Because that was the kind of loop that they are informing us then we still have the queries and we need to ask them again and they are asking you.",
                    "start_time": 21.84,
                    "end_time": 28.24
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So that's why we have set up this meeting so that we can discuss everything with you directly",
                    "start_time": 28.62,
                    "end_time": 33.26
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "also ma'.",
                    "start_time": 35.34,
                    "end_time": 36.34
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Am.",
                    "start_time": 36.34,
                    "end_time": 36.54
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "But we have shared some of the questions with them.",
                    "start_time": 36.86,
                    "end_time": 39.82
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We have not shared this sheet particularly but we have shared directly questions with",
                    "start_time": 40.22,
                    "end_time": 44.82
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "them they are aware about.",
                    "start_time": 44.82,
                    "end_time": 46.38
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah, I think there was some confusion because I think we went back and forth but we didn't understand the actual questions.",
                    "start_time": 47.18,
                    "end_time": 52.42
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Now it seems a bit more clear.",
                    "start_time": 52.42,
                    "end_time": 53.82
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So usually like ONCA and is really used in the balance sheet and the cash flow forecast.",
                    "start_time": 54.46,
                    "end_time": 59.58
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Right.",
                    "start_time": 59.58,
                    "end_time": 59.9
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "I'm trying to see like whether we did use it.",
                    "start_time": 62.38,
                    "end_time": 64.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, no, so I'm looking at onca.",
                    "start_time": 66.46,
                    "end_time": 68.7
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We haven't given long term investments, investment property goodwill.",
                    "start_time": 68.7,
                    "end_time": 74.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We haven't given.",
                    "start_time": 74.22,
                    "end_time": 75.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, I think we can, we haven't given a forecasted formula for it.",
                    "start_time": 80.87,
                    "end_time": 86.39
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So when you can provide that to us because actually the thing is we are still stuck in these kind of things and we are unable to proceed it further.",
                    "start_time": 89.11,
                    "end_time": 96.87
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So it would be good if you feel like that.",
                    "start_time": 97.35,
                    "end_time": 99.67
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, some formulas are required from your end and then you can provide it at your earliest.",
                    "start_time": 99.67,
                    "end_time": 103.83
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, let's go to the next question.",
                    "start_time": 109.52,
                    "end_time": 110.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I can try to give you the formula on this call itself.",
                    "start_time": 110.6,
                    "end_time": 113.12
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And other, my other question is for OCA we have four value in the document.",
                    "start_time": 114.64,
                    "end_time": 119.44
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like one is prepaid open, new prepaid, prepaid amount and prepaid close.",
                    "start_time": 120.24,
                    "end_time": 127.52
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So",
                    "start_time": 128.16,
                    "end_time": 128.56
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "OCA will be prepaid closed.",
                    "start_time": 130.56,
                    "end_time": 132.28
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 132.28,
                    "end_time": 132.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That is telling you the calculation of how to get there from open to close.",
                    "start_time": 132.48,
                    "end_time": 137.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So it's pretty paid.",
                    "start_time": 137.93,
                    "end_time": 139.21
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So how we will calculate it like prepare close minus prepaid open for change in oca.",
                    "start_time": 139.37,
                    "end_time": 145.21
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Change in oca it will be what your prepaid close is from the previous month.",
                    "start_time": 149.13,
                    "end_time": 153.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you're looking at March 2026, you're comparing your March 2026 prepaid close number to February 2026 prepaid close and",
                    "start_time": 154.25,
                    "end_time": 164.21
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "for January we will take from the previous year.",
                    "start_time": 164.21,
                    "end_time": 168.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 168.53,
                    "end_time": 168.93
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "December 2025.",
                    "start_time": 168.93,
                    "end_time": 170.21
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we will take that OC OCA value like in the code, like some of these three.",
                    "start_time": 171.89,
                    "end_time": 181.25
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, so.",
                    "start_time": 181.33,
                    "end_time": 182.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So I think I've given that number as well.",
                    "start_time": 182.01,
                    "end_time": 184.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go to inputs, the inputs tab here in this sheet.",
                    "start_time": 184.17,
                    "end_time": 190.43
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no, no, no, no, no, no.",
                    "start_time": 191.63,
                    "end_time": 192.95
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Go back to the other sheet you're on or even.",
                    "start_time": 192.95,
                    "end_time": 195.67
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 195.67,
                    "end_time": 196.07
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you go to inputs.",
                    "start_time": 196.07,
                    "end_time": 197.39
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I think if you go down.",
                    "start_time": 198.11,
                    "end_time": 201.95
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I think this is where he.",
                    "start_time": 201.95,
                    "end_time": 206.27
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Prepaid opening.",
                    "start_time": 212.84,
                    "end_time": 213.8
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 214.36,
                    "end_time": 214.84
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you have.",
                    "start_time": 214.84,
                    "end_time": 215.52
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 215.52,
                    "end_time": 215.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "26 2.",
                    "start_time": 216.12,
                    "end_time": 217.32
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You have the AR balance, inventory balance, AP balance.",
                    "start_time": 217.64,
                    "end_time": 220.92
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, we've added all that in here.",
                    "start_time": 220.92,
                    "end_time": 222.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I think we like we have to",
                    "start_time": 224.36,
                    "end_time": 226.08
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "only take this sub account value.",
                    "start_time": 226.08,
                    "end_time": 228.28
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes, we gave the balance and then Akash had put in some, some comments right in there because I remember going through this with him in the call a couple of weeks ago.",
                    "start_time": 229.16,
                    "end_time": 238.83
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Just to clarify rhythm.",
                    "start_time": 242.19,
                    "end_time": 243.71
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Actually we need to take into.",
                    "start_time": 244.51,
                    "end_time": 246.07
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "For the oca, we need to take into account for the prepaid close.",
                    "start_time": 246.07,
                    "end_time": 251.07
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "And if you need to calculate for the December 2025, you will need to like take into account all the three other values and add and subtract according to the formula.",
                    "start_time": 251.39,
                    "end_time": 263.11
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Then you will get the value for the December part.",
                    "start_time": 263.11,
                    "end_time": 265.39
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "No, no, no, no, no, no.",
                    "start_time": 266.08,
                    "end_time": 267.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Repaid clothes you already have.",
                    "start_time": 267.4,
                    "end_time": 268.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right?",
                    "start_time": 268.88,
                    "end_time": 269.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You already have the actual number from December 2025.",
                    "start_time": 269.28,
                    "end_time": 271.84
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's what I'm saying.",
                    "start_time": 271.84,
                    "end_time": 272.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "These are from there.",
                    "start_time": 272.6,
                    "end_time": 273.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Do you have it to them?",
                    "start_time": 273.44,
                    "end_time": 274.32
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yep.",
                    "start_time": 274.88,
                    "end_time": 275.36
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are saying to take this value, this account prepaid expenses which come under code OCA for December 2025 and that value is 262141.",
                    "start_time": 275.36,
                    "end_time": 288.16
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 288.88,
                    "end_time": 289.44
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay.",
                    "start_time": 289.92,
                    "end_time": 291.07
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And for my next question is for earnings not in retained earning as I show you there cash flow, change in earnings not attribute to retained income.",
                    "start_time": 295.3,
                    "end_time": 309.86
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So four changes for actual value.",
                    "start_time": 314.18,
                    "end_time": 319.18
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We have this formula used in code by your team.",
                    "start_time": 319.26,
                    "end_time": 323.1
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like change in retain learning and other equity equal to change in other equity plus change in current earning plus change in retained earnings minus these values.",
                    "start_time": 324.14,
                    "end_time": 333.9
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But you only provide us this code.",
                    "start_time": 335.34,
                    "end_time": 338.06
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We do not have any formula to how to calculate for forecasting.",
                    "start_time": 348.71,
                    "end_time": 353.43
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can you show me where that is in the financial statements in the ua?",
                    "start_time": 357.27,
                    "end_time": 363.27
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 363.59,
                    "end_time": 364.07
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Change in earnings.",
                    "start_time": 364.23,
                    "end_time": 365.35
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So this is in cash flow, right?",
                    "start_time": 367.51,
                    "end_time": 368.95
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yep.",
                    "start_time": 370.11,
                    "end_time": 370.59
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "If we have to use the formula used by your team then we need these four values also like change in other equity, change in current earnings, dividends and adjustments like their forecasting values.",
                    "start_time": 382.35,
                    "end_time": 396.44
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So forecasting value for dividends you already have.",
                    "start_time": 397,
                    "end_time": 399.44
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 399.44,
                    "end_time": 399.8
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay.",
                    "start_time": 400.2,
                    "end_time": 400.84
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But we don't have change in other equity and change in current earnings.",
                    "start_time": 404.12,
                    "end_time": 409.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can I see which the code that they're referring to if you go to the source documentation where there is.",
                    "start_time": 411.96,
                    "end_time": 419.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 419.88,
                    "end_time": 420.36
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So change in other equity and change in current earnings.",
                    "start_time": 421.65,
                    "end_time": 424.29
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 424.29,
                    "end_time": 424.85
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So the actual Excel with the financial data, which line items are you, are they referring to in the code?",
                    "start_time": 425.49,
                    "end_time": 432.29
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "In the code your team is using this formula.",
                    "start_time": 439.25,
                    "end_time": 442.93
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 447.5,
                    "end_time": 447.78
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So which account Classifications are they taking.",
                    "start_time": 447.78,
                    "end_time": 450.22
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are taking break for a second.",
                    "start_time": 451.1,
                    "end_time": 454.06
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are taking oeq.",
                    "start_time": 460.46,
                    "end_time": 462.14
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 464.46,
                    "end_time": 465.02
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Dividend div.",
                    "start_time": 465.5,
                    "end_time": 466.94
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Retained earning RA for adjustment.",
                    "start_time": 468.46,
                    "end_time": 471.9
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are taking adjustments.",
                    "start_time": 471.9,
                    "end_time": 473.59
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can you just write these all down so it's clear to us as well?",
                    "start_time": 475.42,
                    "end_time": 479.42
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 480.38,
                    "end_time": 481.02
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "In the document which you created and just write every code in front of the.",
                    "start_time": 481.58,
                    "end_time": 486.3
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 487.74,
                    "end_time": 488.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So then it's.",
                    "start_time": 488.26,
                    "end_time": 489.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's clear",
                    "start_time": 489.02,
                    "end_time": 489.58
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "in the formula only.",
                    "start_time": 492.62,
                    "end_time": 493.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can you.",
                    "start_time": 493.62,
                    "end_time": 494.1
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "In the formula, how we are calculating each value Just in the.",
                    "start_time": 494.1,
                    "end_time": 498.7
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "In the circular braces.",
                    "start_time": 498.7,
                    "end_time": 500.06
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Just write the.",
                    "start_time": 501.01,
                    "end_time": 501.73
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "You can write.",
                    "start_time": 504.93,
                    "end_time": 505.65
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "It.",
                    "start_time": 526.3,
                    "end_time": 526.54
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we need to calculate these forecasting values also to calculate this.",
                    "start_time": 554.87,
                    "end_time": 560.63
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Cediv.",
                    "start_time": 566.47,
                    "end_time": 567.59
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So div.",
                    "start_time": 567.749,
                    "end_time": 568.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You have.",
                    "start_time": 568.55,
                    "end_time": 569.11
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah.",
                    "start_time": 569.35,
                    "end_time": 569.91
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 570.63,
                    "end_time": 571.03
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So can we just put a note that the values you already have.",
                    "start_time": 571.11,
                    "end_time": 573.99
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, so this is already provided.",
                    "start_time": 574.47,
                    "end_time": 576.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Adj.",
                    "start_time": 578.24,
                    "end_time": 578.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We said we're not doing.",
                    "start_time": 578.88,
                    "end_time": 580.04
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 580.04,
                    "end_time": 580.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So we're not forecasting adjustments.",
                    "start_time": 580.72,
                    "end_time": 585
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 585,
                    "end_time": 585.36
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "For forecasting.",
                    "start_time": 585.36,
                    "end_time": 586.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So that's not applicable.",
                    "start_time": 586.88,
                    "end_time": 588.08
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We also have change in retained earnings.",
                    "start_time": 590,
                    "end_time": 592.32
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then we need these two values.",
                    "start_time": 593.6,
                    "end_time": 595.2
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And my last query is for fixed assets.",
                    "start_time": 601.52,
                    "end_time": 603.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, Just one second.",
                    "start_time": 605.83,
                    "end_time": 607.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Is it ce?",
                    "start_time": 612.23,
                    "end_time": 613.03
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I don't see CE as a classification anyway.",
                    "start_time": 613.11,
                    "end_time": 616.15
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It is mentioned in the code there ce.",
                    "start_time": 617.19,
                    "end_time": 620.389
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So I don't.",
                    "start_time": 621.43,
                    "end_time": 622.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you look at the document.",
                    "start_time": 622.11,
                    "end_time": 623.39
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I don't.",
                    "start_time": 623.39,
                    "end_time": 623.71
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Is it CE or re?",
                    "start_time": 623.71,
                    "end_time": 624.87
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Are you sure",
                    "start_time": 625.27,
                    "end_time": 625.91
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "this code in the",
                    "start_time": 629.19,
                    "end_time": 629.95
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "document,",
                    "start_time": 629.95,
                    "end_time": 630.47
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Are you able to define the code and find where it's been applied?",
                    "start_time": 640.6,
                    "end_time": 643.96
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Maybe it was renamed in the code.",
                    "start_time": 644.52,
                    "end_time": 646.519
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Obviously we are not aware.",
                    "start_time": 646.519,
                    "end_time": 647.72
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Like are you able to follow that and see how many times it's been used or in which calculation it was used in the code?",
                    "start_time": 647.88,
                    "end_time": 654.2
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It is used for current earnings prior current running.",
                    "start_time": 656.74,
                    "end_time": 660.98
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "But why is it defined before this or used?",
                    "start_time": 665.94,
                    "end_time": 668.9
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "They are just using this classification code only and they will search it from DB then.",
                    "start_time": 671.3,
                    "end_time": 677.38
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So can you see where they're extracting the.",
                    "start_time": 678.74,
                    "end_time": 680.82
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So we have the db right.",
                    "start_time": 681.22,
                    "end_time": 682.66
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And if we can we see what numbers they're extracting for some particular month so we can see where they're deriving the numbers from?",
                    "start_time": 683.34,
                    "end_time": 690.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "From the Excel db.",
                    "start_time": 690.86,
                    "end_time": 692.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Wait a second.",
                    "start_time": 693.58,
                    "end_time": 694.46
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "I will check.",
                    "start_time": 694.78,
                    "end_time": 695.46
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Prism.",
                    "start_time": 767.53,
                    "end_time": 767.85
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Can you run a query just to find all the data related to CE code only?",
                    "start_time": 767.85,
                    "end_time": 773.37
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yes sir.",
                    "start_time": 773.69,
                    "end_time": 774.41
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It.",
                    "start_time": 785.14,
                    "end_time": 785.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "No, we do not have any count related to that as we will uploading this Excel sheet.",
                    "start_time": 827.23,
                    "end_time": 835.39
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But in this Excel sheet there is no such code.",
                    "start_time": 835.63,
                    "end_time": 839.54
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So it is also not present in the db.",
                    "start_time": 840.02,
                    "end_time": 842.34
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So they're taking no.",
                    "start_time": 844.74,
                    "end_time": 845.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No numbers.",
                    "start_time": 846.18,
                    "end_time": 847.14
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yep.",
                    "start_time": 847.54,
                    "end_time": 848.1
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what's the only number taken then?",
                    "start_time": 848.98,
                    "end_time": 850.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's only taken from oeq.",
                    "start_time": 850.62,
                    "end_time": 853.7
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Is it?",
                    "start_time": 853.7,
                    "end_time": 854.18
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah.",
                    "start_time": 855.14,
                    "end_time": 864.61
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Maybe your team is providing any other Excel sheet using any other Excel sheet.",
                    "start_time": 866.04,
                    "end_time": 873.72
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, it's the same one.",
                    "start_time": 874.28,
                    "end_time": 875.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I'll check with Ashpreet.",
                    "start_time": 875.6,
                    "end_time": 877.16
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah.",
                    "start_time": 877.72,
                    "end_time": 878.12
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then There is no such code in Adobe.",
                    "start_time": 878.12,
                    "end_time": 881.72
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We have this code, but no account related to that.",
                    "start_time": 881.88,
                    "end_time": 885.08
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, so if I, if I take a particular month, what numbers are we using then?",
                    "start_time": 886.36,
                    "end_time": 890.56
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So let's take a number.",
                    "start_time": 890.56,
                    "end_time": 891.72
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Let's take a month like January 2024 for example.",
                    "start_time": 891.8,
                    "end_time": 894.81
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What are the numbers that it's taking to do the calculation based on this code?",
                    "start_time": 895.05,
                    "end_time": 899.21
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Then we can see which numbers they're taking.",
                    "start_time": 899.69,
                    "end_time": 901.85
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then they are just taking this code and use this in this function.",
                    "start_time": 920.42,
                    "end_time": 928.1
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no.",
                    "start_time": 931.46,
                    "end_time": 932.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So can we take an example to see what numbers are taking and based on the code, let's see what numbers are extracting from the db.",
                    "start_time": 932.02,
                    "end_time": 941.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But in a DB we do not have that account.",
                    "start_time": 942.82,
                    "end_time": 945.06
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah, sorry, rhythm.",
                    "start_time": 948.84,
                    "end_time": 950.28
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "For the full formula they have, they have been taking the OEQ and the adj.",
                    "start_time": 950.84,
                    "end_time": 955.32
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So can you calculate value for one month using the other other other data like change in retained earning another equity or there are other three things also?",
                    "start_time": 955.88,
                    "end_time": 968.08
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "No, can you let them, can you show the numbers for others?",
                    "start_time": 968.08,
                    "end_time": 972.68
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Have you understood algorithm what we are saying?",
                    "start_time": 977.68,
                    "end_time": 979.6
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "What was the tag again?",
                    "start_time": 1014.97,
                    "end_time": 1016.01
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Pe or ec?",
                    "start_time": 1016.65,
                    "end_time": 1018.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Ce.",
                    "start_time": 1019.45,
                    "end_time": 1019.85
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So I don't see ce, I see re.",
                    "start_time": 1020.09,
                    "end_time": 1022.25
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "What if maybe instead of EC they meant equity, they meant equity clause.",
                    "start_time": 1026.32,
                    "end_time": 1031.36
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Right?",
                    "start_time": 1032.8,
                    "end_time": 1033.2
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Because.",
                    "start_time": 1033.28,
                    "end_time": 1033.68
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "And then they're taking the equity open",
                    "start_time": 1033.68,
                    "end_time": 1036.24
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "plus the net profit and balance.",
                    "start_time": 1036.24,
                    "end_time": 1040.88
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "They should have been like ec but then they called it the.",
                    "start_time": 1041.92,
                    "end_time": 1045.44
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Because if you go back to the question they want to know like what value do they put in the cash flow statement and.",
                    "start_time": 1047.04,
                    "end_time": 1054.2
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Every month for.",
                    "start_time": 1060.12,
                    "end_time": 1061.16
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay, you guys are trying to calculate the total equity in the balance sheet or what was the question with regard to?",
                    "start_time": 1078.45,
                    "end_time": 1087.41
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "If you go back to the original, original question inside your document.",
                    "start_time": 1090.69,
                    "end_time": 1094.29
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what's the calculation you after number three.",
                    "start_time": 1100.05,
                    "end_time": 1102.53
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "After number three for fixed assets.",
                    "start_time": 1104.46,
                    "end_time": 1107.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no, no, no, no.",
                    "start_time": 1107.42,
                    "end_time": 1108.7
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Change in retaining earning another equity.",
                    "start_time": 1110.62,
                    "end_time": 1112.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We are using change in other equity.",
                    "start_time": 1112.54,
                    "end_time": 1114.94
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "No, no, no.",
                    "start_time": 1115.58,
                    "end_time": 1116.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What's, what's the calculation you're after?",
                    "start_time": 1116.18,
                    "end_time": 1118.14
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "This is a formula.",
                    "start_time": 1118.14,
                    "end_time": 1119.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What is the actual calc.",
                    "start_time": 1119.18,
                    "end_time": 1120.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What are you, what are we calculating?",
                    "start_time": 1120.26,
                    "end_time": 1121.66
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Earnings.",
                    "start_time": 1128.87,
                    "end_time": 1129.27
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Not in retained earnings.",
                    "start_time": 1129.27,
                    "end_time": 1131.07
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Wouldn't that be equity?",
                    "start_time": 1131.07,
                    "end_time": 1133.19
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah, I will show you in ui.",
                    "start_time": 1134.23,
                    "end_time": 1136.63
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, So it's under financing activities.",
                    "start_time": 1137.59,
                    "end_time": 1144.55
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, just going to the Excel.",
                    "start_time": 1148.31,
                    "end_time": 1150.55
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So shall we proceed with the next query?",
                    "start_time": 1174.72,
                    "end_time": 1176.56
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Just one second.",
                    "start_time": 1178.24,
                    "end_time": 1179.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1179.85,
                    "end_time": 1180.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, let's go to the next query.",
                    "start_time": 1215.94,
                    "end_time": 1217.1
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We'll come back to these two.",
                    "start_time": 1217.1,
                    "end_time": 1218.34
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah, the next queries.",
                    "start_time": 1218.58,
                    "end_time": 1221.419
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "For fixed assets, as you mentioned in the sheet, for sub account we need to use PP closing and total depreciation from capex.",
                    "start_time": 1221.419,
                    "end_time": 1233.71
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "But for actual value for property and equipment or for accumulated depreciation, which code we will refer.",
                    "start_time": 1235.63,
                    "end_time": 1246.03
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like under FA code we have four sub Accounts like land and building, plant and machinery, furniture, equipment, or computer equipments.",
                    "start_time": 1247.39,
                    "end_time": 1256.99
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So all this will come under property and equipments.",
                    "start_time": 1259.21,
                    "end_time": 1262.65
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Correct.",
                    "start_time": 1263.21,
                    "end_time": 1263.77
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And for accumulated depreciation, for actual, we have depth code which has amortization and depreciation.",
                    "start_time": 1264.49,
                    "end_time": 1274.97
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So should we use depth code for that?",
                    "start_time": 1275.69,
                    "end_time": 1278.09
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like I show you, in this financial sheet, we have code dep.",
                    "start_time": 1281.53,
                    "end_time": 1284.95
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And DEP has six sub accounts.",
                    "start_time": 1286.55,
                    "end_time": 1288.79
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Go back to the ui because we shouldn't.",
                    "start_time": 1290.07,
                    "end_time": 1293.75
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1294.23,
                    "end_time": 1294.63
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you go, where are we looking?",
                    "start_time": 1294.63,
                    "end_time": 1295.99
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's balance sheet, right?",
                    "start_time": 1296.23,
                    "end_time": 1297.59
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1303.67,
                    "end_time": 1304.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So we shouldn't have accumulated depreciation as a line item here to begin with.",
                    "start_time": 1304.11,
                    "end_time": 1309.35
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So this accumulated depreciation, this wasn't in Ashpreet's code, which is a question he was asking if you've merged the code.",
                    "start_time": 1313.13,
                    "end_time": 1319.81
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Because this accumulated depreciation row was never there and never calculated in the output he had produced.",
                    "start_time": 1319.81,
                    "end_time": 1330.73
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So we should.",
                    "start_time": 1334.33,
                    "end_time": 1335.13
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We should not have accumulated appreciation.",
                    "start_time": 1335.41,
                    "end_time": 1337.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Your question on property and equipment is, basically, there's four accounts.",
                    "start_time": 1337.41,
                    "end_time": 1341.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1341.65,
                    "end_time": 1342.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "The answer to that, this accumulated depreciation should not be there.",
                    "start_time": 1342.01,
                    "end_time": 1345.65
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 1346.37,
                    "end_time": 1346.89
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So we shall remove it from the UI as well and we can just focus on the property and equipment for now.",
                    "start_time": 1346.89,
                    "end_time": 1352.77
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1353.33,
                    "end_time": 1353.81
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, got it.",
                    "start_time": 1354.05,
                    "end_time": 1355.65
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And for fixed asset, the sum of this is fixed asset.",
                    "start_time": 1355.89,
                    "end_time": 1360.37
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Closing balance.",
                    "start_time": 1365.13,
                    "end_time": 1365.81
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "My nice.",
                    "start_time": 1365.81,
                    "end_time": 1366.69
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Accumulated depreciation equal to fixed assets.",
                    "start_time": 1366.69,
                    "end_time": 1369.69
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1370.57,
                    "end_time": 1371.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1371.21,
                    "end_time": 1371.69
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we are not calculating this.",
                    "start_time": 1372.09,
                    "end_time": 1373.77
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So this means fixed assets is equal to PP closing balance.",
                    "start_time": 1374.41,
                    "end_time": 1377.529
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Correct.",
                    "start_time": 1378.17,
                    "end_time": 1378.73
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay,",
                    "start_time": 1379.21,
                    "end_time": 1379.85
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "that's all from my side.",
                    "start_time": 1382.09,
                    "end_time": 1383.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1385.93,
                    "end_time": 1386.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go to the top, don't stop sharing.",
                    "start_time": 1386.33,
                    "end_time": 1389.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you had your question on onca, right?",
                    "start_time": 1389.66,
                    "end_time": 1392.3
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah.",
                    "start_time": 1393.18,
                    "end_time": 1393.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for.",
                    "start_time": 1395.74,
                    "end_time": 1396.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for onca, what you can use is to keep it simple.",
                    "start_time": 1396.26,
                    "end_time": 1401.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You can use the same numbers from the previous year.",
                    "start_time": 1401.02,
                    "end_time": 1403.34
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So ONCA has three items, right?",
                    "start_time": 1403.98,
                    "end_time": 1406.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It has goodwill, investment property, long term investments.",
                    "start_time": 1406.02,
                    "end_time": 1409.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You can use the Same numbers from 2025.",
                    "start_time": 1410.46,
                    "end_time": 1414.46
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay.",
                    "start_time": 1415.2,
                    "end_time": 1415.68
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1416.32,
                    "end_time": 1416.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "As your forecasted numbers for now.",
                    "start_time": 1417.12,
                    "end_time": 1418.96
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So there's only one pending question, right?",
                    "start_time": 1435.2,
                    "end_time": 1437.04
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay,",
                    "start_time": 1438.48,
                    "end_time": 1439.04
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "yeah.",
                    "start_time": 1441.04,
                    "end_time": 1441.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Only one pending question, is it?",
                    "start_time": 1441.44,
                    "end_time": 1442.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's right.",
                    "start_time": 1442.76,
                    "end_time": 1443.24
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go back to that one pending question.",
                    "start_time": 1443.24,
                    "end_time": 1445.52
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Just one.",
                    "start_time": 1445.76,
                    "end_time": 1446.47
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "One second.",
                    "start_time": 1446.54,
                    "end_time": 1446.94
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Can you share your screen?",
                    "start_time": 1447.26,
                    "end_time": 1448.18
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "One second, please.",
                    "start_time": 1448.18,
                    "end_time": 1448.94
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what's the one pending question that we have?",
                    "start_time": 1456.06,
                    "end_time": 1458.46
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Not this one rhythm, the third one.",
                    "start_time": 1458.94,
                    "end_time": 1460.54
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, yeah.",
                    "start_time": 1464.3,
                    "end_time": 1466.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go to the Excel, because what you're doing is you're calculating your cash flow for your financing activities, go to the Excel and go to the cash flow tab here.",
                    "start_time": 1466.26,
                    "end_time": 1478.89
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you can see in column J, you have your financing cash flow from financing activities.",
                    "start_time": 1482.01,
                    "end_time": 1488.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You have the formula here.",
                    "start_time": 1488.41,
                    "end_time": 1489.85
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you go into it, You are getting all the numbers right that you have.",
                    "start_time": 1490.49,
                    "end_time": 1502.33
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay.",
                    "start_time": 1504.41,
                    "end_time": 1505.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you follow it to what it's calculating.",
                    "start_time": 1506.65,
                    "end_time": 1509.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "These are then your rows basically that you'll get that how you're getting your cash flow from financing activities.",
                    "start_time": 1509.13,
                    "end_time": 1515.69
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "That.",
                    "start_time": 1530.5,
                    "end_time": 1530.66
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Okay, can you repeat that question again?",
                    "start_time": 1530.66,
                    "end_time": 1534.18
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Go to the Excel, go to the sheet again and then click on the cell on.",
                    "start_time": 1536.26,
                    "end_time": 1540.82
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Click on the cell.",
                    "start_time": 1541.22,
                    "end_time": 1542.18
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay, now instead of.",
                    "start_time": 1542.18,
                    "end_time": 1543.34
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah, just click once and then go to the, the top of the bar and then you click on CAPEX that you see F83 or any of the values, just click.",
                    "start_time": 1543.34,
                    "end_time": 1552.94
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Click on one of them.",
                    "start_time": 1553.01,
                    "end_time": 1553.81
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah, they're up there.",
                    "start_time": 1554.45,
                    "end_time": 1555.33
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Up there where you are.",
                    "start_time": 1555.33,
                    "end_time": 1556.29
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So he's saying you should basically, if you want to know the exact calculation and where the source data is coming from, when you click there, you should be able to highlight on this sheet where it's coming from and then use that as the same formula to understand the, the value, the output.",
                    "start_time": 1557.09,
                    "end_time": 1574.37
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Click on it once.",
                    "start_time": 1575.33,
                    "end_time": 1576.17
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Like click on an entire like CAPEX 32 83.",
                    "start_time": 1576.17,
                    "end_time": 1580.29
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Maybe pick one.",
                    "start_time": 1580.29,
                    "end_time": 1582.8
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Click on D83.",
                    "start_time": 1584.56,
                    "end_time": 1585.76
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It's not there.",
                    "start_time": 1592.8,
                    "end_time": 1593.56
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "I think",
                    "start_time": 1593.56,
                    "end_time": 1594
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "it'll Highlight.",
                    "start_time": 1597.68,
                    "end_time": 1598.56
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "This is D83, 4.",
                    "start_time": 1601.2,
                    "end_time": 1602.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1607.05,
                    "end_time": 1607.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you follow the formulas, it gives you all the numbers it's taking, right?",
                    "start_time": 1607.33,
                    "end_time": 1611.25
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "As a, as a calculation, there was C67, D67, C83.",
                    "start_time": 1611.25,
                    "end_time": 1617.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you go, you'll see there about four or five.",
                    "start_time": 1617.29,
                    "end_time": 1619.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right, so it's telling you which rows and what it's taking to derive the number.",
                    "start_time": 1620.89,
                    "end_time": 1626.41
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So it.",
                    "start_time": 1628.17,
                    "end_time": 1628.73
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We are calculating this, this earning like we have retained.",
                    "start_time": 1628.97,
                    "end_time": 1636.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, go to the ui.",
                    "start_time": 1637.38,
                    "end_time": 1638.74
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yeah,",
                    "start_time": 1639.06,
                    "end_time": 1639.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "go to the cash flow.",
                    "start_time": 1642.34,
                    "end_time": 1643.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You are calculating financing activities, right?",
                    "start_time": 1645.06,
                    "end_time": 1647.7
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Cash flow from financing activities.",
                    "start_time": 1647.779,
                    "end_time": 1649.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you have got all the, the numbers there, right?",
                    "start_time": 1650.26,
                    "end_time": 1654.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "To do.",
                    "start_time": 1654.22,
                    "end_time": 1654.66
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "To, to get to your number,",
                    "start_time": 1654.66,
                    "end_time": 1655.86
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "All the sub items.",
                    "start_time": 1660.98,
                    "end_time": 1662.34
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "You're saying that we have this, this and this.",
                    "start_time": 1664.66,
                    "end_time": 1667.62
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we will minus.",
                    "start_time": 1668.58,
                    "end_time": 1670.02
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then we will calculate financing financing activity.",
                    "start_time": 1670.42,
                    "end_time": 1674.02
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We will minus this.",
                    "start_time": 1674.26,
                    "end_time": 1675.38
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Then we will get change in earning, not attribute to retaining income.",
                    "start_time": 1675.54,
                    "end_time": 1679.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no, no, what I'm saying is from your.",
                    "start_time": 1680.58,
                    "end_time": 1682.58
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You have sub line items that you can take your calculation from.",
                    "start_time": 1687.39,
                    "end_time": 1690.99
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's what I'm saying.",
                    "start_time": 1691.07,
                    "end_time": 1691.95
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you follow that formula, you have five, five numbers that it's relating to, right?",
                    "start_time": 1691.95,
                    "end_time": 1697.47
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you have all the numbers, right?",
                    "start_time": 1697.79,
                    "end_time": 1700.27
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And if you're summing them all up, you get your total, which is your financing activities.",
                    "start_time": 1700.27,
                    "end_time": 1704.59
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay, can you go to Rashid once again?",
                    "start_time": 1705.55,
                    "end_time": 1711.88
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Let me just see that formula.",
                    "start_time": 1712.12,
                    "end_time": 1713.64
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Financial cfa.",
                    "start_time": 1717,
                    "end_time": 1718.28
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Let's just write it down.",
                    "start_time": 1720.84,
                    "end_time": 1722
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right, so let's look at C67 and D67.",
                    "start_time": 1722,
                    "end_time": 1725.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Actually write down what?",
                    "start_time": 1725.2,
                    "end_time": 1726.36
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, so what are C67 and D67?",
                    "start_time": 1727,
                    "end_time": 1729.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Why don't you actually write down.",
                    "start_time": 1729.48,
                    "end_time": 1730.84
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Great, yeah, write down the names, right, basically of what?",
                    "start_time": 1731.64,
                    "end_time": 1736.44
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "C67 83 +E83F83.",
                    "start_time": 1736.44,
                    "end_time": 1743
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "D67.",
                    "start_time": 1748.44,
                    "end_time": 1749.56
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It's new loans here.",
                    "start_time": 1752.12,
                    "end_time": 1754.68
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "D67 is repayments.",
                    "start_time": 1755.72,
                    "end_time": 1758.44
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1758.84,
                    "end_time": 1759.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So it's short term debt.",
                    "start_time": 1759.2,
                    "end_time": 1760.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1761,
                    "end_time": 1761.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you can see it says short term debt above.",
                    "start_time": 1761.4,
                    "end_time": 1763.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1763.88,
                    "end_time": 1764.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So short term debt repayments.",
                    "start_time": 1764.44,
                    "end_time": 1766.12
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay.",
                    "start_time": 1766.96,
                    "end_time": 1767.28
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "D83 owner funding, F83 dividends.",
                    "start_time": 1768.32,
                    "end_time": 1778.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 1779.68,
                    "end_time": 1780.16
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So it's D and then ENF.",
                    "start_time": 1780.56,
                    "end_time": 1782.639
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1782.639,
                    "end_time": 1782.96
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So.",
                    "start_time": 1782.96,
                    "end_time": 1783.36
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "And one is external funding.",
                    "start_time": 1783.6,
                    "end_time": 1785.2
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "External funding and then dividends.",
                    "start_time": 1785.28,
                    "end_time": 1787.44
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So those are your.",
                    "start_time": 1791.44,
                    "end_time": 1792.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's your breakdown of how you get to your financing activities.",
                    "start_time": 1792.93,
                    "end_time": 1796.45
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So what I would recommend if you",
                    "start_time": 1797.49,
                    "end_time": 1799.49
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "actually like.",
                    "start_time": 1801.57,
                    "end_time": 1802.69
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We already calculated change in short term depth and change in long term depth.",
                    "start_time": 1802.69,
                    "end_time": 1806.93
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like can you properly.",
                    "start_time": 1812.05,
                    "end_time": 1813.69
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like we have we like in the.",
                    "start_time": 1813.69,
                    "end_time": 1816.57
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Before calculating the total financial activities.",
                    "start_time": 1816.57,
                    "end_time": 1818.93
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1819.52,
                    "end_time": 1819.76
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So you are saying that this is the formula and this will be the total value.",
                    "start_time": 1819.76,
                    "end_time": 1822.96
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "But to calculate the only the change in earning note attribute retained income.",
                    "start_time": 1823.52,
                    "end_time": 1827.28
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We don't know like which.",
                    "start_time": 1827.28,
                    "end_time": 1828.56
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Which column we should highlight from which column this or which code we need to take into account to calculate the.",
                    "start_time": 1828.56,
                    "end_time": 1834.48
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Just this part only.",
                    "start_time": 1834.48,
                    "end_time": 1835.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like to calculate total financial activity.",
                    "start_time": 1838.48,
                    "end_time": 1840.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "You guys told that this is the formula and this is the columns you need to take into account.",
                    "start_time": 1840.44,
                    "end_time": 1844.08
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "But like in the change in earning.",
                    "start_time": 1844.64,
                    "end_time": 1847.41
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Not every tender.",
                    "start_time": 1847.41,
                    "end_time": 1848.53
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like with what data?",
                    "start_time": 1848.61,
                    "end_time": 1850.89
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like we need to calculate this from.",
                    "start_time": 1850.89,
                    "end_time": 1852.37
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no.",
                    "start_time": 1852.77,
                    "end_time": 1853.29
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what I'm saying is your financing activities make up of those five balances.",
                    "start_time": 1853.29,
                    "end_time": 1857.49
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So there's something.",
                    "start_time": 1857.97,
                    "end_time": 1859.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "There's something that's happened.",
                    "start_time": 1859.17,
                    "end_time": 1860.77
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Either you've merged the code because these items are not there in what Ashpreet had given.",
                    "start_time": 1860.77,
                    "end_time": 1865.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "This change in earnings not attributed to retained income was never there.",
                    "start_time": 1865.65,
                    "end_time": 1869.49
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Actually this is the mockup ui.",
                    "start_time": 1870.05,
                    "end_time": 1874.92
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We.",
                    "start_time": 1874.92,
                    "end_time": 1875.24
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We can't change to this part.",
                    "start_time": 1875.24,
                    "end_time": 1876.68
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So it was there before.",
                    "start_time": 1877.16,
                    "end_time": 1879.4
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Only we haven't changed in the mocked ui.",
                    "start_time": 1879.4,
                    "end_time": 1881.16
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It's provided from your side only.",
                    "start_time": 1881.16,
                    "end_time": 1882.68
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It was there starting.",
                    "start_time": 1882.68,
                    "end_time": 1884.52
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 1884.52,
                    "end_time": 1884.92
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no.",
                    "start_time": 1884.92,
                    "end_time": 1885.32
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So what I'm saying is current uses five items that we've just gone through.",
                    "start_time": 1885.32,
                    "end_time": 1890.279
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Follow the formulas.",
                    "start_time": 1890.279,
                    "end_time": 1891.32
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1891.56,
                    "end_time": 1892.12
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1892.12,
                    "end_time": 1892.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So you want to that like in the financial activities.",
                    "start_time": 1892.44,
                    "end_time": 1895
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We should mention those five points here.",
                    "start_time": 1895.4,
                    "end_time": 1897.56
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Not these ones.",
                    "start_time": 1897.56,
                    "end_time": 1898.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes.",
                    "start_time": 1898.92,
                    "end_time": 1899.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1900.77,
                    "end_time": 1901.05
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Got it.",
                    "start_time": 1901.05,
                    "end_time": 1901.57
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 1902.21,
                    "end_time": 1902.77
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So those five points are new loans, short term debt.",
                    "start_time": 1905.17,
                    "end_time": 1909.81
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's owner funding, external funding.",
                    "start_time": 1910.21,
                    "end_time": 1913.09
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And then you have the last one which was.",
                    "start_time": 1913.49,
                    "end_time": 1917.01
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Repayments dividends.",
                    "start_time": 1921.97,
                    "end_time": 1924.21
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Not this one.",
                    "start_time": 1927.74,
                    "end_time": 1928.38
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no.",
                    "start_time": 1929.02,
                    "end_time": 1929.74
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay, sir.",
                    "start_time": 1930.3,
                    "end_time": 1931.1
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah, we go.",
                    "start_time": 1935.34,
                    "end_time": 1935.94
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "There we go.",
                    "start_time": 1935.94,
                    "end_time": 1936.54
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We have.",
                    "start_time": 1936.86,
                    "end_time": 1937.5
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We have to use these exact value.",
                    "start_time": 1938.06,
                    "end_time": 1939.98
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "We have to use like change in new loans or change in loan close or change in dividends.",
                    "start_time": 1939.98,
                    "end_time": 1945.94
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like this.",
                    "start_time": 1945.94,
                    "end_time": 1946.54
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Let me answer.",
                    "start_time": 1948.78,
                    "end_time": 1949.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You're calculating the cash flow.",
                    "start_time": 1949.9,
                    "end_time": 1951.5
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you are asking you.",
                    "start_time": 1951.5,
                    "end_time": 1953.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You are calculating the.",
                    "start_time": 1953.18,
                    "end_time": 1954.7
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Go back to the Excel.",
                    "start_time": 1955.55,
                    "end_time": 1956.91
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Note the movement for.",
                    "start_time": 1964.75,
                    "end_time": 1966.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "For that particular month.",
                    "start_time": 1966.11,
                    "end_time": 1967.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, it's for the.",
                    "start_time": 1970.59,
                    "end_time": 1971.95
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's for those months.",
                    "start_time": 1971.95,
                    "end_time": 1972.91
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "What they're saying is you need to take the.",
                    "start_time": 1976.67,
                    "end_time": 1978.99
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like.",
                    "start_time": 1979.15,
                    "end_time": 1979.55
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Suppose this is the.",
                    "start_time": 1979.55,
                    "end_time": 1980.83
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like this is the value and these are drive from these five values.",
                    "start_time": 1980.99,
                    "end_time": 1983.75
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1983.75,
                    "end_time": 1984.11
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "And these are the actual values.",
                    "start_time": 1984.68,
                    "end_time": 1986.84
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So you need to like you need to take into account these actual values.",
                    "start_time": 1987,
                    "end_time": 1990.68
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Get their change in values for every month and then we need to show it over there you have the.",
                    "start_time": 1990.84,
                    "end_time": 1996.04
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, no, these are the actual values.",
                    "start_time": 1996.84,
                    "end_time": 1998.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 1998.4,
                    "end_time": 1998.6
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So your actual value.",
                    "start_time": 1998.6,
                    "end_time": 1999.56
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for example.",
                    "start_time": 1999.56,
                    "end_time": 2000.519
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "No, this is forecasted values.",
                    "start_time": 2000.52,
                    "end_time": 2003.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, yeah.",
                    "start_time": 2004.12,
                    "end_time": 2004.88
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you're forecasted.",
                    "start_time": 2004.88,
                    "end_time": 2006.08
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for your cash flow from financing activities, your forecasted value for Jan 2026 will be 20,000.",
                    "start_time": 2006.08,
                    "end_time": 2014.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Go back to the UI.",
                    "start_time": 2014.34,
                    "end_time": 2015.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, so that will be minus 20,000.",
                    "start_time": 2017.14,
                    "end_time": 2019.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 2019.22,
                    "end_time": 2019.5
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So here in financing activities in blue you will have minus 20,000 and then the breakdown you'll have is.",
                    "start_time": 2019.5,
                    "end_time": 2025.5
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You'll have that breakdown of what those.",
                    "start_time": 2025.5,
                    "end_time": 2027.38
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What those five items are.",
                    "start_time": 2028.26,
                    "end_time": 2029.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 2029.74,
                    "end_time": 2030.02
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "How does minus 20,000 break down from.",
                    "start_time": 2030.1,
                    "end_time": 2032.58
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Okay, okay, I got it.",
                    "start_time": 2033.22,
                    "end_time": 2034.5
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Actually I was just trying to say that in here we are showing the change in values.",
                    "start_time": 2034.66,
                    "end_time": 2040.56
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We are not showing the actual forecasted values.",
                    "start_time": 2040.56,
                    "end_time": 2043
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So it will be not shown as here 20000 it will be subtract.",
                    "start_time": 2043.4,
                    "end_time": 2047.8
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Suppose we are showing the May value here.",
                    "start_time": 2047.8,
                    "end_time": 2050.12
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It will be subtracted first and then that value will be shown here.",
                    "start_time": 2050.12,
                    "end_time": 2053.88
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Or do you want to show the actual just the forecasted value there only you don't want to show the change values here.",
                    "start_time": 2054.68,
                    "end_time": 2060.04
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Change in like as we are doing we are subtracting the of the previous month.",
                    "start_time": 2060.04,
                    "end_time": 2064.16
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Then we're showing here like we have",
                    "start_time": 2064.16,
                    "end_time": 2066.57
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "already done for change in short term depth or change in long term depth.",
                    "start_time": 2066.57,
                    "end_time": 2070.21
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "I mean I. I believe you should be showing the.",
                    "start_time": 2073.49,
                    "end_time": 2075.89
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "The forecasted values and then the variance is what shows the change.",
                    "start_time": 2076.13,
                    "end_time": 2079.81
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Correct?",
                    "start_time": 2081.49,
                    "end_time": 2082.13
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Right.",
                    "start_time": 2082.21,
                    "end_time": 2082.53
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "But yeah, so the variance column like at the last.",
                    "start_time": 2082.53,
                    "end_time": 2086.05
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "At the end, that's where usually changes.",
                    "start_time": 2086.21,
                    "end_time": 2088.53
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah, we can do that also.",
                    "start_time": 2089.73,
                    "end_time": 2091.01
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Sure.",
                    "start_time": 2091.319,
                    "end_time": 2091.559
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like for change in short term, long term depth we are using this formula like loan open from depth calculation for Jan 2026 minus December 2025.",
                    "start_time": 2092.679,
                    "end_time": 2105.159
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Can we do this on WhatsApp?",
                    "start_time": 2106.359,
                    "end_time": 2108.679
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Simran, are you looking at WhatsApp?",
                    "start_time": 2108.999,
                    "end_time": 2110.999
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, yes.",
                    "start_time": 2112.039,
                    "end_time": 2112.839
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So that's what we are proposing.",
                    "start_time": 2114.839,
                    "end_time": 2116.839
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, you have shared an example.",
                    "start_time": 2118.27,
                    "end_time": 2120.03
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yes.",
                    "start_time": 2120.99,
                    "end_time": 2121.47
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, let me share that with my team so that they can have a look at it.",
                    "start_time": 2123.39,
                    "end_time": 2126.75
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Just a second.",
                    "start_time": 2130.19,
                    "end_time": 2130.91
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "I am doing it on a quality.",
                    "start_time": 2131.31,
                    "end_time": 2132.91
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So I mean the example is Excel, right?",
                    "start_time": 2148.92,
                    "end_time": 2151.24
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "The current calculation shows it's 20,000 and that's how it ended up as 20,000 because of the addition or subtraction of Those items.",
                    "start_time": 2151.48,
                    "end_time": 2159.24
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay.",
                    "start_time": 2161.4,
                    "end_time": 2162.04
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "So instead of writing the line as change in,",
                    "start_time": 2164.04,
                    "end_time": 2166.44
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "we can show directly.",
                    "start_time": 2169,
                    "end_time": 2170.2
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We can show directly the.",
                    "start_time": 2170.2,
                    "end_time": 2171.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 2174.34,
                    "end_time": 2174.54
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And then the variance column is your change.",
                    "start_time": 2174.54,
                    "end_time": 2176.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 2176.18,
                    "end_time": 2176.54
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you can see what that number was from this month versus last month.",
                    "start_time": 2176.54,
                    "end_time": 2179.9
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And then that is your change in number.",
                    "start_time": 2179.9,
                    "end_time": 2181.94
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right?",
                    "start_time": 2181.94,
                    "end_time": 2182.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You.",
                    "start_time": 2182.26,
                    "end_time": 2182.62
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You subtracting the current.",
                    "start_time": 2182.62,
                    "end_time": 2183.86
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Current.",
                    "start_time": 2184.26,
                    "end_time": 2184.66
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Current month's number from the previous month's number.",
                    "start_time": 2184.9,
                    "end_time": 2187.54
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yep, we have got it.",
                    "start_time": 2187.62,
                    "end_time": 2188.82
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "The screenshot, ma', am, I've shared.",
                    "start_time": 2189.54,
                    "end_time": 2191.86
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 2192.18,
                    "end_time": 2192.58
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Can you please check the group first?",
                    "start_time": 2192.58,
                    "end_time": 2194.1
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "No, no, local group.",
                    "start_time": 2195.22,
                    "end_time": 2196.42
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 2196.42,
                    "end_time": 2196.9
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2200.59,
                    "end_time": 2200.99
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We don't want to show rhythm changes, actual forecasted values and the variance will show what are the changes values.",
                    "start_time": 2201.47,
                    "end_time": 2208.99
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2208.99,
                    "end_time": 2209.39
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "And like we have to do it",
                    "start_time": 2211.47,
                    "end_time": 2213.709
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "for all of this.",
                    "start_time": 2213.709,
                    "end_time": 2215.15
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Like",
                    "start_time": 2215.71,
                    "end_time": 2216.11
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "we are also showing change in other current liabilities, change in account payables, change in inventories.",
                    "start_time": 2218.51,
                    "end_time": 2223.31
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "So we have to show forecasted value or change in values.",
                    "start_time": 2224.29,
                    "end_time": 2228.85
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "For under cash flow.",
                    "start_time": 2230.21,
                    "end_time": 2232.17
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "It is like for operating activities, like change in account payables, change in other current liabilities, change in account receivables.",
                    "start_time": 2232.17,
                    "end_time": 2243.49
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, that, no, that is correct.",
                    "start_time": 2244.85,
                    "end_time": 2246.45
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "For operating activities that you have to show the change change.",
                    "start_time": 2246.45,
                    "end_time": 2249.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That is correct.",
                    "start_time": 2249.41,
                    "end_time": 2250.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2250.25,
                    "end_time": 2250.69
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2250.69,
                    "end_time": 2251.13
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Like for fine activities, we have to show only forecasted values.",
                    "start_time": 2252.01,
                    "end_time": 2256.65
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 2257.61,
                    "end_time": 2258.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2258.81,
                    "end_time": 2259.45
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Yes, sir.",
                    "start_time": 2270.41,
                    "end_time": 2271.05
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Thank you.",
                    "start_time": 2273.29,
                    "end_time": 2273.93
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2276.1,
                    "end_time": 2276.58
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you, if you look at that cash flow, indirect Excel, right.",
                    "start_time": 2277.62,
                    "end_time": 2280.82
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It gives you the entire formulas of how to calculate your, your cash flow, right?",
                    "start_time": 2280.82,
                    "end_time": 2285.18
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You just have to follow those formulas and what numbers it's linking to.",
                    "start_time": 2285.18,
                    "end_time": 2288.34
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right?",
                    "start_time": 2288.34,
                    "end_time": 2288.58
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And you will get the numbers.",
                    "start_time": 2288.58,
                    "end_time": 2289.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You will get what numbers you have to apply for a change versus what you just take as a forecast.",
                    "start_time": 2290.82,
                    "end_time": 2295.78
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Numbers.",
                    "start_time": 2295.78,
                    "end_time": 2296.22
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right, Just that Excel we've given.",
                    "start_time": 2296.22,
                    "end_time": 2297.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You just need to follow it.",
                    "start_time": 2297.74,
                    "end_time": 2299.06
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, right.",
                    "start_time": 2299.3,
                    "end_time": 2300.1
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And it links through the different tabs of what numbers it's picking up and what accounts is picking up from.",
                    "start_time": 2300.33,
                    "end_time": 2305.45
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You just have to follow that for one month.",
                    "start_time": 2305.45,
                    "end_time": 2308.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So you understand and then you can apply that for the month.",
                    "start_time": 2308.57,
                    "end_time": 2311.13
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Sure.",
                    "start_time": 2311.69,
                    "end_time": 2312.09
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 2312.17,
                    "end_time": 2312.65
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Ma'.",
                    "start_time": 2319.45,
                    "end_time": 2319.73
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Am.",
                    "start_time": 2319.73,
                    "end_time": 2319.93
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So with us there was, with all.",
                    "start_time": 2320.65,
                    "end_time": 2322.89
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's the forecasting queries, right?",
                    "start_time": 2323.13,
                    "end_time": 2325.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Were there any.",
                    "start_time": 2325.41,
                    "end_time": 2326.01
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "These were all the forecasting queries.",
                    "start_time": 2326.33,
                    "end_time": 2328.25
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So now given these queries, what's the latest timeline?",
                    "start_time": 2329.32,
                    "end_time": 2333.4
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Simran for once you've built it and tested it internally with your QA before you hand over to us, what's your update timeline there?",
                    "start_time": 2333.4,
                    "end_time": 2342.36
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "See, I can provide the updated timelines in some time so that we can discuss and then we can plan accordingly.",
                    "start_time": 2342.36,
                    "end_time": 2350.36
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "That what.",
                    "start_time": 2350.36,
                    "end_time": 2350.92
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "How much time it will require.",
                    "start_time": 2350.92,
                    "end_time": 2352.52
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "And apart from this, we need to work upon the security points and the unit testing as well.",
                    "start_time": 2352.52,
                    "end_time": 2358.2
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So I will accumulate the meeting with my internal team and then we can provide you with the timelines.",
                    "start_time": 2358.36,
                    "end_time": 2363.96
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2364.36,
                    "end_time": 2364.8
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for module two it is just a forecasted financials page which is pending.",
                    "start_time": 2364.8,
                    "end_time": 2369.72
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "The other pages are done.",
                    "start_time": 2369.72,
                    "end_time": 2370.92
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 2371.32,
                    "end_time": 2371.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You attached the other pages?",
                    "start_time": 2371.76,
                    "end_time": 2373.32
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah, See we.",
                    "start_time": 2373.72,
                    "end_time": 2374.84
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "You can't check it out because the thing is that we have.",
                    "start_time": 2374.84,
                    "end_time": 2377.68
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We are updating the pusher to socket IO regarding which I need to discuss related everything with Ashbit.",
                    "start_time": 2377.68,
                    "end_time": 2383.8
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "That's why I just want him to join the meeting because he just provided us with his feedback so we have some kind of queries on his feedback because these are some more of the enhancements instead of the changes because we have to put the extra efforts and that will even extend the deadline too.",
                    "start_time": 2383.8,
                    "end_time": 2402.2
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So that was my only concern, that he should join the meeting so that we can have a discussion in the same call and then we can finalize everything.",
                    "start_time": 2402.6,
                    "end_time": 2410.12
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, I'm just messaging him so he can join.",
                    "start_time": 2415.24,
                    "end_time": 2417.64
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Also I'm informing my two other team members who are working on a zero part and plus who are working on the socket IO so that they can discuss everything related to the feedback and whatever enhancements and architecture changes that Ashprit is asking for.",
                    "start_time": 2420.36,
                    "end_time": 2436.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "The document that Ashpreet sent with the fee.",
                    "start_time": 2437.31,
                    "end_time": 2440.27
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2450.19,
                    "end_time": 2450.749
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Any.",
                    "start_time": 2450.99,
                    "end_time": 2451.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Any concerns you had on that.",
                    "start_time": 2451.31,
                    "end_time": 2452.59
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We have documented we have two documents, one with his feedback and other one with the R responses to that feedback.",
                    "start_time": 2454.19,
                    "end_time": 2463.09
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, yeah, just bring it up.",
                    "start_time": 2463.33,
                    "end_time": 2468.89
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Let's see if there's anything Gomy or I can maybe answer while he joins.",
                    "start_time": 2468.89,
                    "end_time": 2473.33
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah, sure.",
                    "start_time": 2473.65,
                    "end_time": 2475.73
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, yes.",
                    "start_time": 2482.37,
                    "end_time": 2483.17
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "As rhythm is not working on these.",
                    "start_time": 2483.41,
                    "end_time": 2486.57
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "These kind of things.",
                    "start_time": 2486.57,
                    "end_time": 2487.57
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So he can left the meeting for now because he's working more focused on the forecast module so he can continue his work.",
                    "start_time": 2487.57,
                    "end_time": 2493.61
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Right?",
                    "start_time": 2493.61,
                    "end_time": 2493.93
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yeah, that's right.",
                    "start_time": 2496.97,
                    "end_time": 2497.65
                },
                {
                    "speaker_name": "Rhythm jalhotra",
                    "text": "Thank you everyone.",
                    "start_time": 2497.65,
                    "end_time": 2498.25
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah, thank you so much.",
                    "start_time": 2498.49,
                    "end_time": 2501.21
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Niha, please open the document they do with the ashpit feedback and plus that you have created the two of the documents.",
                    "start_time": 2518.74,
                    "end_time": 2527.06
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2527.54,
                    "end_time": 2528.18
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "And firstly share your screen with the one with the ashp feedback.",
                    "start_time": 2528.42,
                    "end_time": 2532.98
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So Bhavnit Neha is a front end developer and Manish the back end developer.",
                    "start_time": 2536.02,
                    "end_time": 2540.1
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Hi bhavniti.",
                    "start_time": 2544.43,
                    "end_time": 2552.11
                },
                {
                    "speaker_name": "Neha",
                    "text": "Is my screen visible?",
                    "start_time": 2560.51,
                    "end_time": 2561.71
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Yes.",
                    "start_time": 2564.91,
                    "end_time": 2565.39
                },
                {
                    "speaker_name": "Neha",
                    "text": "So I have gone through this third document and.",
                    "start_time": 2582.2,
                    "end_time": 2585.72
                },
                {
                    "speaker_name": "Neha",
                    "text": "And we have implemented like a double Q system.",
                    "start_time": 2593.97,
                    "end_time": 2598.77
                },
                {
                    "speaker_name": "Neha",
                    "text": "Now dashboard is saying that we should go with the Redis pub sub which will be a better approach.",
                    "start_time": 2598.93,
                    "end_time": 2604.05
                },
                {
                    "speaker_name": "Neha",
                    "text": "And I have gone done some R D like Socket IO the W also a better approach.",
                    "start_time": 2605.57,
                    "end_time": 2613.33
                },
                {
                    "speaker_name": "Neha",
                    "text": "Just the redis is like messaging queue like when the consumer completes the task.",
                    "start_time": 2614.85,
                    "end_time": 2621.74
                },
                {
                    "speaker_name": "Neha",
                    "text": "Redis P also give the responses a little bit too fast as compared to the double Q.",
                    "start_time": 2622.46,
                    "end_time": 2628.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So",
                    "start_time": 2634.38,
                    "end_time": 2634.78
                },
                {
                    "speaker_name": "Neha",
                    "text": "WQ is also a better approach.",
                    "start_time": 2637.1,
                    "end_time": 2638.78
                },
                {
                    "speaker_name": "Neha",
                    "text": "We just share the timeline as well.",
                    "start_time": 2639.1,
                    "end_time": 2641.94
                },
                {
                    "speaker_name": "Neha",
                    "text": "That the recommendation which I provided by the split so will take our two working days off.",
                    "start_time": 2641.94,
                    "end_time": 2647.79
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay so I think Ashprit has just sent me a message.",
                    "start_time": 2650.51,
                    "end_time": 2653.19
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "He just stuck in a meeting.",
                    "start_time": 2653.19,
                    "end_time": 2654.27
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can we do 2:30 India time and in the meantime these your responses to his feedback.",
                    "start_time": 2654.35,
                    "end_time": 2660.39
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If you just share it on the WhatsApp group he can look at it in the meantime and then Simran if you can just put in a call at 2:30 Indian time which is 1 o' clock UA time.",
                    "start_time": 2660.39,
                    "end_time": 2672.55
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 2673.19,
                    "end_time": 2673.55
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And then can join and then the full and then you and Aspreet and the full team can go through that and and come to a decision.",
                    "start_time": 2673.55,
                    "end_time": 2679.91
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah sure it works for us.",
                    "start_time": 2680.23,
                    "end_time": 2682.55
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We can join it at 2:30.",
                    "start_time": 2682.71,
                    "end_time": 2684.47
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "All right then I'm sharing the new meeting invite for 2:30pm IST.",
                    "start_time": 2688.79,
                    "end_time": 2692.63
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, yeah right.",
                    "start_time": 2693.35,
                    "end_time": 2695.03
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "And apart from this we will try to provide you with the time estimations for the forecast module.",
                    "start_time": 2695.35,
                    "end_time": 2700.96
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah and then the scenario modeling.",
                    "start_time": 2701.92,
                    "end_time": 2703.76
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Do you how is that coming along module 3?",
                    "start_time": 2703.76,
                    "end_time": 2706.32
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "See module 3 is totally focused and.",
                    "start_time": 2706.64,
                    "end_time": 2710.72
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Because a lot of, because a lot of the calculations you're using in module 3 are derived from module 2 right?",
                    "start_time": 2715.2,
                    "end_time": 2720.48
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, yes these are all overlapped or interlinked.",
                    "start_time": 2720.72,
                    "end_time": 2723.52
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So that's why if we have to work upon the few forecast financials in the forecast module and then we can only check with the scenario modeling and once it is done then only we can finalize both of the modules as these are interlinked.",
                    "start_time": 2723.52,
                    "end_time": 2738
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So we will provide you with the time estimations of both the modules for now because scenario modeling is done but for now the socket IO regarding which we need to discuss discuss with Ashpreet and once it is finalized then we can provide you with that handover of scenario modeling.",
                    "start_time": 2744.72,
                    "end_time": 2760.33
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 2761.69,
                    "end_time": 2762.25
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 2762.57,
                    "end_time": 2762.93
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Okay.",
                    "start_time": 2762.93,
                    "end_time": 2763.25
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And was there anything on the AI plan that you wanted to discuss or that with Raheel and that's with Raheel",
                    "start_time": 2763.25,
                    "end_time": 2769.73
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "and Akash they were I believe they had discussion with Ashbay related to the second approach rack based approach for the AI module and we haven't get any feedback that with which approach we need to proceeded further.",
                    "start_time": 2769.73,
                    "end_time": 2781.06
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So I believe they will provide us an insight on which approach we have to proceed it.",
                    "start_time": 2781.54,
                    "end_time": 2787.22
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "If you have an idea then you can let me know because we are stuck in the AM audience.",
                    "start_time": 2787.54,
                    "end_time": 2791.38
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No, I think our approach is.",
                    "start_time": 2796.339,
                    "end_time": 2797.86
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, go ahead.",
                    "start_time": 2797.86,
                    "end_time": 2798.58
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Well I mean I recommend that we we still need a little bit of a discussion on our side and then we'll get back to you asap.",
                    "start_time": 2800.42,
                    "end_time": 2806.22
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2807.25,
                    "end_time": 2807.73
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, no problem.",
                    "start_time": 2807.89,
                    "end_time": 2808.93
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Then you can have your discussion and then you can let us know Still I want to highlight it here that when one you inform us that with each approach we will need to proceed it further.",
                    "start_time": 2808.93,
                    "end_time": 2820.13
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "According to that, I'll provide you with the timeline for the AI module.",
                    "start_time": 2820.37,
                    "end_time": 2823.73
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Right.",
                    "start_time": 2825.73,
                    "end_time": 2826.13
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So it all if any kind of changes in the architecture or whenever we get the clarifications just now, we have get clarification the forecast module.",
                    "start_time": 2828.45,
                    "end_time": 2838.21
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So we will work on the forecast financials.",
                    "start_time": 2838.21,
                    "end_time": 2841.05
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So according to that the deadlines would be changed.",
                    "start_time": 2841.13,
                    "end_time": 2844.81
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "That's why I'm just informing you just an insight for you to that once we get an approval on the approach for the AI module, then only we will start working on it.",
                    "start_time": 2845.05,
                    "end_time": 2855.45
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes.",
                    "start_time": 2858.49,
                    "end_time": 2858.99
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, that's noted.",
                    "start_time": 2859.22,
                    "end_time": 2860.3
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That's fine.",
                    "start_time": 2860.3,
                    "end_time": 2860.82
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2860.82,
                    "end_time": 2861.3
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "All right.",
                    "start_time": 2861.3,
                    "end_time": 2861.86
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So let's connect it to 30 then.",
                    "start_time": 2862.1,
                    "end_time": 2863.78
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "All right, thanks.",
                    "start_time": 2864.98,
                    "end_time": 2865.78
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, thank you.",
                    "start_time": 2866.1,
                    "end_time": 2866.98
                },
                {
                    "speaker_name": "Ngũmi Gituro",
                    "text": "Bye.",
                    "start_time": 2869.62,
                    "end_time": 2870.18
                }
            ],
              "summary": {
                "keywords": [
                    "forecasting",
                    "cash flow",
                    "ONCA",
                    "financing activities",
                    "database codes",
                    "Socket.IO"
                ],
                "action_items": "\n**Project Manager SFS**\nProvide updated delivery timelines for forecast module after internal QA, security, and unit testing (39:02)\nShare Ashpreet’s architectural feedback documents and coordinate team to address Socket.IO implementation and feedback (40:20)\nOrganize follow-up meeting at 14:30 IST to discuss architectural feedback and finalize decisions with Ashpreet and team (44:40)\nProvide timeline estimations for both forecast and scenario modeling modules once Socket.IO discussion is resolved (45:06)\n\n**Bhavneet Mhajan**\nProvide missing forecast formulas for ONCA items and clarify formulas during the call (01:29)\nDocument and clarify classification codes used in cash flow forecasting formulas to ensure alignment with database fields (07:55)\nConfirm exclusion of accumulated depreciation from UI and balance sheet output (21:04)\nExplain financing activities cash flow breakdown and formula components clearly to team (24:01)\nGuide team to use forecast actual values in UI and variance column to show monthly changes (33:54)\nConfirm that forecast numbers for ONCA items can use prior year’s data as base (23:15)\nHighlight to team to follow existing indirect cash flow Excel workbook formulas for correct cash flow forecast calculations (37:57)\n\n**Rhythm Jalhotra**\nValidate and provide actual sub-account values for prepaid expenses and link to OCA changes (01:54)\nProvide clarity on codes used for change in earnings not attributed to retained income and forecast components (04:48)\nConfirm removal or resolution of “CE” code ambiguity and database mappings (10:05)\nConfirm fixed assets formula use with property and equipment only and accumulated depreciation exclusion (20:18)\nShare screenshots and data to clarify forecast vs. changes for short and long-term debts and other financing activities components (30:02)\n\n**Ngũmi Gituro**\nRecommend showing forecasted values in cash flow with variance column for changes to aid clarity (34:33)\nSuggest tracing database extracts for example months to clarify source of forecast inputs (14:38)\n\n**Neha**\nPresent analysis of Redis pub/sub versus double queue system for messaging; estimate two days to implement recommended Redis approach (42:40)\n",
                "overview": "- **Forecasting Formulas Clarified:** Team aligned on key forecasting sources for cash flow and balance sheet to reduce confusion.\n\n- **Investment Data Usage Confirmed:** ONCA will use 2025 forecasted numbers as placeholders for goodwill and investment property, simplifying calculations.\n\n- **Module Development Progress:** Only the forecasted financials page remains incomplete; timelines will be reviewed post internal QA.\n\n- **AI Module on Hold:** Development awaits strategic decisions on approach and architecture, impacting resource allocation and timelines.\n\n- **Improved Communication Practices:** Direct discussions with stakeholders enhance decision-making speed and transparency, reducing previous delays.",
                "outline": "null"
              }
            },
            {
              "id": "01KMHQSBYB1RAGY2X4EP6DCMC9",
              "title": "Nolocode AI meeting",
              "dateString": "2026-03-25T05:34:27.000Z",
              "sentences": [
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "It.",
                    "start_time": 0.16,
                    "end_time": 0.4
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "So I think everyone's joining in about five to ten minutes.",
                    "start_time": 32.41,
                    "end_time": 35.05
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Probably less.",
                    "start_time": 35.69,
                    "end_time": 36.49
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "But yeah, if anyone wants to get tea, coffee or anything before we start then have some time so feel free to do so.",
                    "start_time": 37.05,
                    "end_time": 45.77
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "No, no, we are good to go.",
                    "start_time": 46.41,
                    "end_time": 47.61
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "If you want to have that then you can.",
                    "start_time": 47.61,
                    "end_time": 49.53
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Yeah sure.",
                    "start_time": 52.34,
                    "end_time": 52.9
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "I think I need it.",
                    "start_time": 52.98,
                    "end_time": 54.02
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Then you can have it.",
                    "start_time": 55.38,
                    "end_time": 56.5
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Your voice saying that you need it.",
                    "start_time": 56.74,
                    "end_time": 58.82
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 59.54,
                    "end_time": 60.02
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Thank you.",
                    "start_time": 60.02,
                    "end_time": 60.66
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "I'll be back.",
                    "start_time": 60.66,
                    "end_time": 61.46
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Five minutes.",
                    "start_time": 61.62,
                    "end_time": 62.26
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Sure.",
                    "start_time": 62.26,
                    "end_time": 62.66
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 62.66,
                    "end_time": 63.3
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Good morning everyone.",
                    "start_time": 101.55,
                    "end_time": 102.35
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Very good morning, how are you?",
                    "start_time": 104.45,
                    "end_time": 108.53
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We are just waiting for Ashpirit to join and then we can key off the meeting.",
                    "start_time": 118.45,
                    "end_time": 121.81
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay.",
                    "start_time": 124.45,
                    "end_time": 125.09
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So do we have Raheel and a.",
                    "start_time": 125.25,
                    "end_time": 127.49
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, Akash is available and he will join in around five minutes.",
                    "start_time": 128.57,
                    "end_time": 132.41
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Hi guys.",
                    "start_time": 206.76,
                    "end_time": 207.32
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Morning.",
                    "start_time": 207.4,
                    "end_time": 207.8
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Good morning.",
                    "start_time": 212.44,
                    "end_time": 213
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah I'm doing great.",
                    "start_time": 214.04,
                    "end_time": 216.68
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Who are we waiting for now?",
                    "start_time": 218.84,
                    "end_time": 220.68
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We are waiting for Ashpree.",
                    "start_time": 221.8,
                    "end_time": 223.36
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Once he joins then we can start with the meeting.",
                    "start_time": 223.36,
                    "end_time": 225.32
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "All right.",
                    "start_time": 225.64,
                    "end_time": 226.16
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 226.16,
                    "end_time": 226.68
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Hi Badnet, do you want to check with Ashpeed when is he joining?",
                    "start_time": 522,
                    "end_time": 526.08
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, just give him a couple of minutes.",
                    "start_time": 527.2,
                    "end_time": 529.12
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, thank you.",
                    "start_time": 529.36,
                    "end_time": 530.72
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Hi guys.",
                    "start_time": 564.42,
                    "end_time": 564.98
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah, hi, how are you?",
                    "start_time": 567.7,
                    "end_time": 569.46
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Okay so I think we have everyone now, right?",
                    "start_time": 576.9,
                    "end_time": 579.14
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 579.62,
                    "end_time": 580.02
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Right.",
                    "start_time": 580.02,
                    "end_time": 580.34
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Okay so if we can then begin with first like do you have direct questions Ashby Bhavni or should we give you an overview of the first approach and then the second one and we can help you compare and contrast between them.",
                    "start_time": 582.66,
                    "end_time": 598.44
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, we can quickly like summarize the two approaches or what is the proposed approach.",
                    "start_time": 605.72,
                    "end_time": 613.08
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 613.32,
                    "end_time": 613.8
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Okay so yeah Simran is harsh going to take the lead here or.",
                    "start_time": 613.96,
                    "end_time": 618.78
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah sure can take the lead and he can confirm everything related to the first approach and the second approach.",
                    "start_time": 619.02,
                    "end_time": 624.46
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay so hello everyone.",
                    "start_time": 624.94,
                    "end_time": 626.86
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So I'm sharing my screen and then I will explain the both approaches.",
                    "start_time": 628.94,
                    "end_time": 633.66
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Is my screen visible to everyone?",
                    "start_time": 642.71,
                    "end_time": 644.23
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes, it's visible.",
                    "start_time": 645.19,
                    "end_time": 646.39
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay so like I will explain using this diagram.",
                    "start_time": 646.39,
                    "end_time": 652.31
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we in our chatbot we have multiple types of queries.",
                    "start_time": 653.83,
                    "end_time": 658.79
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So some queries are related to like what today the data which is present in database like revenue and other things.",
                    "start_time": 659.27,
                    "end_time": 667.99
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Some queries are regarding the like the applications and.",
                    "start_time": 668.57,
                    "end_time": 673.93
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And what are the formulas using.",
                    "start_time": 674.09,
                    "end_time": 675.53
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Some queries are regarding the stress test.",
                    "start_time": 675.53,
                    "end_time": 677.61
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So depending on these types of query we handled these things differently in our flow.",
                    "start_time": 678.41,
                    "end_time": 684.81
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So in.",
                    "start_time": 685.21,
                    "end_time": 685.65
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "In this is the previous approach which I am showing to you.",
                    "start_time": 685.65,
                    "end_time": 688.97
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So in the previous approach when whenever the user query was coming to the chatbot the chat was classifying the user query into a stress test query like this query.",
                    "start_time": 689.37,
                    "end_time": 701.52
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "We need to perform stress test on this query or this query belong to other things like regarding the database and general query.",
                    "start_time": 702.08,
                    "end_time": 710.24
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So if it is stress test query then it is go it was going to into different flow.",
                    "start_time": 712.24,
                    "end_time": 718
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like there was a separate flow for the stress test which, which I will explain now.",
                    "start_time": 718.4,
                    "end_time": 723.2
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then if it is not a stress test query then it was going in a different like it will get the data from database and answer on that.",
                    "start_time": 723.84,
                    "end_time": 733.6
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So now let me explain how the stress test being implemented in the previous approach.",
                    "start_time": 734.24,
                    "end_time": 739.759
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So here it is explained.",
                    "start_time": 742.4,
                    "end_time": 744.08
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, so in the previous approach we were getting a concise explanation of about the stress test.",
                    "start_time": 744.64,
                    "end_time": 755.31
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "What is the stress test is about what are the input providing.",
                    "start_time": 755.71,
                    "end_time": 759.23
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "The stress is explained here for example in the recession playbook is a stress test.",
                    "start_time": 759.23,
                    "end_time": 766.59
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we will, we were getting like what will be the input required to execute this test test?",
                    "start_time": 767.23,
                    "end_time": 772.91
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "What are the reasoning which need to be performed to get out from these tests and what are the output format we need to to show in the output what are the graphs and the summary and other things.",
                    "start_time": 773.31,
                    "end_time": 784.96
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we in the like before like including stress test we will, we will be needing our document in the previous approach.",
                    "start_time": 785.52,
                    "end_time": 795.12
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So our document should contain again inputs business logic and failure condition and expected output with an example.",
                    "start_time": 795.84,
                    "end_time": 802.64
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So after we get these things regarding the stress test then we were like understanding the logic and coding it into the repository in the repo in a different folder.",
                    "start_time": 803.52,
                    "end_time": 818.42
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So for every stress test we were creating a separate Python file which includes the logic we need to be implemented for that stress test.",
                    "start_time": 818.42,
                    "end_time": 828.78
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we were identifying what are the inputs regard need to execute the stress and we we were writing queries to get this input from the database.",
                    "start_time": 829.66,
                    "end_time": 839.75
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then we were implementing the logic for this test test and so, and then implementing it.",
                    "start_time": 839.75,
                    "end_time": 847.19
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So after the whole like logic is implemented, another extra step needed to this that add the that stress test into the query classification prompt.",
                    "start_time": 847.19,
                    "end_time": 859.59
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So as I already told you in the first step we were classifying the user query according to stresses.",
                    "start_time": 860.42,
                    "end_time": 868.26
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So if we have five stress tests then we will be needing like five types of stress test in the classification.",
                    "start_time": 868.82,
                    "end_time": 876.82
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So for every stress test a new classification need to be added in that query classification prompt before after writing its logic.",
                    "start_time": 876.9,
                    "end_time": 886.33
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So in the previous approach first we need a document.",
                    "start_time": 886.57,
                    "end_time": 890.57
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then by understanding document we were creating a Python file implementing all the logic from the document.",
                    "start_time": 890.65,
                    "end_time": 896.53
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then we will we were adding a classification regarding that stress test and then we were writing unit test cases and verifying it.",
                    "start_time": 896.53,
                    "end_time": 904.01
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then yeah, that's how we were integrating the stress test into the chat flow previously.",
                    "start_time": 904.41,
                    "end_time": 911.05
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So like in the final step the chat like after the classification, after the query is classified that this query is need to be executed into the using stress test, then it will be routed to that Python function which will which we have created regarding the stress and the response will be come from that function and will be shown to the user.",
                    "start_time": 912.68,
                    "end_time": 938.6
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Now let me show you a demo of this implementation.",
                    "start_time": 939.73,
                    "end_time": 943.25
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "This is the previous approach.",
                    "start_time": 945.25,
                    "end_time": 946.53
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Just go down.",
                    "start_time": 952.45,
                    "end_time": 953.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I wanted to see the pros and cons you had below the document of the previous approach.",
                    "start_time": 953.17,
                    "end_time": 958.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Can we just go through that before?",
                    "start_time": 959.25,
                    "end_time": 960.69
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So I think it will be better if I explain both approaches first, then we can go through this.",
                    "start_time": 962.61,
                    "end_time": 966.85
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, or I can go just for approach one.",
                    "start_time": 968.12,
                    "end_time": 971.96
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 972.12,
                    "end_time": 972.52
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 972.52,
                    "end_time": 972.92
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So like for approach one, like it is, it will obviously be faster because all the logic is already implemented and and queries are already written for that.",
                    "start_time": 973.56,
                    "end_time": 983.279
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So it will be very much fast and token usage will be less because already logic is written and it will not be retrieved from Vector store.",
                    "start_time": 983.279,
                    "end_time": 991.8
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And since if, if I stress this include a very complex logic, then it will be handled properly because a developer will be handling all the test cases here.",
                    "start_time": 992.12,
                    "end_time": 1002.58
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "The only cons for this approach is like it's required to for every new new test to be included, it required to add a new Python file in the repository and then again deploy the code and then test it.",
                    "start_time": 1003.22,
                    "end_time": 1018.1
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So that, that is the cons here.",
                    "start_time": 1018.75,
                    "end_time": 1020.39
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And these are the force for the approach 1.",
                    "start_time": 1020.39,
                    "end_time": 1023.07
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So in your view, harsh.",
                    "start_time": 1024.43,
                    "end_time": 1025.87
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "If you were to, if you were",
                    "start_time": 1025.87,
                    "end_time": 1027.27
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "to create a new a sixth preset question that would require a new code, right?",
                    "start_time": 1027.27,
                    "end_time": 1032.79
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "How long would that take in your estimate for developer to do that?",
                    "start_time": 1032.79,
                    "end_time": 1036.67
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, create another five preset questions.",
                    "start_time": 1037.39,
                    "end_time": 1041.55
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So I have five of them and I want to create another five to get to 10.",
                    "start_time": 1041.55,
                    "end_time": 1044.43
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, so we have implemented the recession Playbook stress test and it took around like three days to implement it properly.",
                    "start_time": 1045.15,
                    "end_time": 1052.59
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So like it was actually complex too.",
                    "start_time": 1053.47,
                    "end_time": 1055.87
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So if I stress test is easy to implement, it will take around like two days, but generally it is taking three days to implement a new stress test.",
                    "start_time": 1055.95,
                    "end_time": 1066.03
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So three days per preset question.",
                    "start_time": 1067.79,
                    "end_time": 1070.27
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So five.",
                    "start_time": 1070.87,
                    "end_time": 1071.71
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Then that's 15 days.",
                    "start_time": 1071.71,
                    "end_time": 1072.95
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "15 working days.",
                    "start_time": 1073.43,
                    "end_time": 1074.63
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yes, you can see.",
                    "start_time": 1076.79,
                    "end_time": 1078.39
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Let's have a look at the demo.",
                    "start_time": 1084.87,
                    "end_time": 1086.39
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, So this is the chatbot.",
                    "start_time": 1087.67,
                    "end_time": 1096.15
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "I am asking the question here.",
                    "start_time": 1097.17,
                    "end_time": 1098.85
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Let me refresh.",
                    "start_time": 1100.77,
                    "end_time": 1101.97
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "It.",
                    "start_time": 1121.98,
                    "end_time": 1122.22
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, see this time response is written in 31 seconds.",
                    "start_time": 1148.15,
                    "end_time": 1153.67
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So the response is, the question was if the market dips and we miss revenue by 20% from quarter three, what do we need to cut or delete to survive next four months?",
                    "start_time": 1155.27,
                    "end_time": 1164.47
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So it analyzed the current situation and provided the mitigation plan along with that, all the scenario like shown in the graph as well.",
                    "start_time": 1165.11,
                    "end_time": 1173.19
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And after that recommendation and assumption for this stress test.",
                    "start_time": 1173.83,
                    "end_time": 1177.83
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So this is the previous like approach on implementation of recession playbook Stress test.",
                    "start_time": 1178.71,
                    "end_time": 1184.63
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 1187.19,
                    "end_time": 1187.83
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I just want to read each of the four points one by one.",
                    "start_time": 1187.83,
                    "end_time": 1190.39
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 1190.71,
                    "end_time": 1191.35
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 1194.79,
                    "end_time": 1195.51
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So yeah.",
                    "start_time": 1196.63,
                    "end_time": 1198.07
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "First like without mitigation the company starting cash balance of AED is this and below target is minimum cash flow of aed.",
                    "start_time": 1198.15,
                    "end_time": 1207.45
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "The company fails to meet its survival target from month one under the recession scenario.",
                    "start_time": 1209.37,
                    "end_time": 1214.69
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Second is mitigation plan.",
                    "start_time": 1214.69,
                    "end_time": 1216.25
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "The recommended mitigation enrolls are 20% reduction in operating expenses and a 50% reduction in capital expenditure.",
                    "start_time": 1217.05,
                    "end_time": 1225.21
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "This plan increase the minimum cash balance to AED this and successfully exceeding the requirement floor ensuring survival.",
                    "start_time": 1225.69,
                    "end_time": 1234.01
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Also the graph includes the base scenario and the minimum cash flow which is used here to compare and with with mitigation.",
                    "start_time": 1234.41,
                    "end_time": 1243.41
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "What will be the effect after mitigation?",
                    "start_time": 1243.41,
                    "end_time": 1245.61
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So graph is showing this and then there there are recommendations like secure immediate short term liquidity through credit lines or equity to bridge the initial cash shortfall and meet the minimum floor.",
                    "start_time": 1246.25,
                    "end_time": 1258.25
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Conduct a comprehensive cost structure to review and identify additional efficiency opportunity beyond the current mitigation.",
                    "start_time": 1259.57,
                    "end_time": 1267.89
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And the third one and after that the assumption which are used in this.",
                    "start_time": 1267.89,
                    "end_time": 1273.17
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So the this analysis assumes a minus 20 revenue drop starting month 1 unchanged COGS, percentage stable working capital timing and no changes to the tax or external funding.",
                    "start_time": 1273.57,
                    "end_time": 1285.73
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Where we got the minimum cash flow balance from?",
                    "start_time": 1289.75,
                    "end_time": 1292.23
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Sorry, can you repeat the question?",
                    "start_time": 1293.27,
                    "end_time": 1294.71
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Where have you got the minimum cash flow balance?",
                    "start_time": 1295.99,
                    "end_time": 1298.71
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I said the minimum cash cash flow balance was 2.2 million.",
                    "start_time": 1298.71,
                    "end_time": 1302.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Where have you got that number from?",
                    "start_time": 1302.87,
                    "end_time": 1304.31
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "I think we are using a formula for this.",
                    "start_time": 1305.43,
                    "end_time": 1308.23
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Let me confirm.",
                    "start_time": 1308.47,
                    "end_time": 1309.43
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Minimum cash flow.",
                    "start_time": 1320.12,
                    "end_time": 1321.8
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, minimum care.",
                    "start_time": 1322.04,
                    "end_time": 1323
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "For calculating minimum cash flow we are using one rate into the Runway months.",
                    "start_time": 1323,
                    "end_time": 1327.24
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So these value are present in the db.",
                    "start_time": 1328.04,
                    "end_time": 1330.28
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So using that we are calculating minimum cash flow.",
                    "start_time": 1330.28,
                    "end_time": 1333
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Any other question and how does that",
                    "start_time": 1342.93,
                    "end_time": 1346.05
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "number compare to the current cash balance?",
                    "start_time": 1346.13,
                    "end_time": 1348.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Cash balance was half of that.",
                    "start_time": 1349.49,
                    "end_time": 1351.05
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Right.",
                    "start_time": 1351.05,
                    "end_time": 1351.41
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Current cash balance 1 second.",
                    "start_time": 1354.129,
                    "end_time": 1358.21
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You are.",
                    "start_time": 1371.4,
                    "end_time": 1371.8
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, I have to look into into it.",
                    "start_time": 1371.96,
                    "end_time": 1376.44
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "The whole data is coming from the db.",
                    "start_time": 1376.68,
                    "end_time": 1379.28
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So the number are directly like this logic is getting number directly from dv.",
                    "start_time": 1379.28,
                    "end_time": 1385.56
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So for that I have to look into the.",
                    "start_time": 1385.88,
                    "end_time": 1387.8
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "As in my question is if the actual cash balance is half of that how do we have a minimum cash flow as double if the existing cash balance is the same.",
                    "start_time": 1397.09,
                    "end_time": 1406.61
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "And the question is we want to survive the next 12 months so we have the existing cash balance.",
                    "start_time": 1406.61,
                    "end_time": 1413.37
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "How can we have a cash floor which is double up on a forecasted cash out cash balances.",
                    "start_time": 1413.37,
                    "end_time": 1420.94
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay,",
                    "start_time": 1425.5,
                    "end_time": 1426.14
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "and just when you go up, if you look at the mix it says 20 reduction in opex and 50 reduction capex.",
                    "start_time": 1428.46,
                    "end_time": 1437.14
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What were the different mixes?",
                    "start_time": 1437.14,
                    "end_time": 1440.46
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right, it's come within.",
                    "start_time": 1440.46,
                    "end_time": 1441.5
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah, it's Come with the recommended mitigation of 20 in Opex and 50 it must have come up with various different combinations, right?",
                    "start_time": 1442.02,
                    "end_time": 1449.9
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "What were the different combinations and how did it arrive to that 20 and 50.",
                    "start_time": 1449.9,
                    "end_time": 1456.5
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, so currently we are not storing that all the com on like combination which are returned by the logic.",
                    "start_time": 1458.02,
                    "end_time": 1466.1
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "But the arrival to the final combination is based on the pen score logic we have implemented.",
                    "start_time": 1466.1,
                    "end_time": 1473.35
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we are assigning every like scenario combination of pain score.",
                    "start_time": 1473.83,
                    "end_time": 1478.71
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So based on that it is like getting to the final conclusion.",
                    "start_time": 1478.79,
                    "end_time": 1482.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Is it applying a criteria?",
                    "start_time": 1487.27,
                    "end_time": 1488.79
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "How is it coming to a conclusion to say the best option is a 20 reduction in optics.",
                    "start_time": 1488.79,
                    "end_time": 1494.15
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, I think we have a document regarding this.",
                    "start_time": 1494.55,
                    "end_time": 1500.01
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Let me show you.",
                    "start_time": 1500.33,
                    "end_time": 1501.61
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Oh, I can see the logic directly here.",
                    "start_time": 1503.29,
                    "end_time": 1506.01
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Give me a second.",
                    "start_time": 1506.25,
                    "end_time": 1507.13
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Document.",
                    "start_time": 1511.77,
                    "end_time": 1512.49
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "This one?",
                    "start_time": 1541.14,
                    "end_time": 1541.62
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah,",
                    "start_time": 1545.3,
                    "end_time": 1545.78
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah.",
                    "start_time": 1561.47,
                    "end_time": 1561.79
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we are using this logic to get to the like the best combination out of the like survive scenarios.",
                    "start_time": 1562.27,
                    "end_time": 1569.63
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So OPEX for OPEX we are assigning this pin score for capex this and then we are like calculating pin score for every survive scenario and picking the best one out of that.",
                    "start_time": 1571.07,
                    "end_time": 1581.92
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay, let's go to the Unless if Ashpreet or Gomi have any other questions, I think I'm okay to go to the second approach.",
                    "start_time": 1588.32,
                    "end_time": 1601.36
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, let's go.",
                    "start_time": 1606.25,
                    "end_time": 1606.97
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So the problem with the first approach was it for every stress test we need to implement it manually and change in the repo and then need to make it live again.",
                    "start_time": 1614.41,
                    "end_time": 1627.53
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So that was the major issue.",
                    "start_time": 1628.26,
                    "end_time": 1629.42
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "For that we start searching for a scalable solution which is in which",
                    "start_time": 1629.42,
                    "end_time": 1635.54
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "it",
                    "start_time": 1638.18,
                    "end_time": 1638.46
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "is easy to add another stress test and can be integrated in the flow automatically.",
                    "start_time": 1638.46,
                    "end_time": 1643.7
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So for that we came up with this approach.",
                    "start_time": 1644.58,
                    "end_time": 1646.9
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "It is a two step process.",
                    "start_time": 1647.14,
                    "end_time": 1649.14
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So in the first step the document is still required.",
                    "start_time": 1650.1,
                    "end_time": 1656.1
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So I will directly explain it how the new test case will be inserted in this approach.",
                    "start_time": 1656.26,
                    "end_time": 1661.42
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, implementation strategy.",
                    "start_time": 1663.34,
                    "end_time": 1666.14
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, so in this approach first initial requirement is still the same.",
                    "start_time": 1673.18,
                    "end_time": 1678.86
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "A document will be required with all the necessary input.",
                    "start_time": 1679.1,
                    "end_time": 1682.46
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "After that document will be processed into the markdown format by an agent.",
                    "start_time": 1683.1,
                    "end_time": 1688.95
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Previously, what the developer is like processing document in the python file.",
                    "start_time": 1688.95,
                    "end_time": 1695.19
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Now this work will be done by an agent in a pipeline.",
                    "start_time": 1695.43,
                    "end_time": 1698.87
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So document processing step will be done by agent and it will generate a python function regarding that stress test and then the agent is run will run that stress test within a provided example by referring to the initial document provided by the financial expert and then validate the file generated function.",
                    "start_time": 1699.27,
                    "end_time": 1720.51
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then if the function is validated, then the that function is indexed into the vector store and will be available to the answer generating agent.",
                    "start_time": 1720.51,
                    "end_time": 1730.75
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And if if the like the generated function is not Validated then it will be flagged for correction.",
                    "start_time": 1731.15,
                    "end_time": 1736.91
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So I will explain this via flow diagram.",
                    "start_time": 1737.47,
                    "end_time": 1740.59
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Now give me a second.",
                    "start_time": 1740.59,
                    "end_time": 1741.99
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So yeah, so the first step of this flow is like storing document in the vector vector database.",
                    "start_time": 1754.79,
                    "end_time": 1760.99
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So I have already explained this a document is needed Agent will process the document summarize and create a python python file for that or a python function.",
                    "start_time": 1760.99,
                    "end_time": 1771.74
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then if the then execute that function on the user provided example.",
                    "start_time": 1772.3,
                    "end_time": 1777.1
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "If the out if the output is correct then it will index that function along with the summary.",
                    "start_time": 1777.1,
                    "end_time": 1783.54
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And if it is incorrect then flag the document for manual verification.",
                    "start_time": 1783.54,
                    "end_time": 1787.66
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So this is first step of the second approach.",
                    "start_time": 1788.06,
                    "end_time": 1790.22
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then how it will be integrated when agent is generating the answer.",
                    "start_time": 1790.86,
                    "end_time": 1795.58
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So here user query will be analyzed like user query.",
                    "start_time": 1796,
                    "end_time": 1802.64
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Based on the user query relevant document will be fetched from the vector database.",
                    "start_time": 1803.28,
                    "end_time": 1808.48
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So then agent will will look like compare the user query with the relevant document.",
                    "start_time": 1808.88,
                    "end_time": 1813.92
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So so if the user user query is about stress test and like the input required for the stress test also available in the query then it will go ahead and like start executing the stress test.",
                    "start_time": 1814.08,
                    "end_time": 1828.19
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Else it will like answer the query based on the retrieval document.",
                    "start_time": 1828.19,
                    "end_time": 1832.07
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like it it could be about the application on the formula or other things.",
                    "start_time": 1832.07,
                    "end_time": 1836.99
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So now if the query is about stress test agent will gather all the input required to execute stress test test using a query to SQL tool.",
                    "start_time": 1837.63,
                    "end_time": 1848.19
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "It will fetch all the data from the database and then execute the stress test using that function which is which we previously stored in the vector database.",
                    "start_time": 1848.19,
                    "end_time": 1860.19
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then the result generated from that function will be like shown to the user like yeah, this will be like updated flow.",
                    "start_time": 1863.07,
                    "end_time": 1873.39
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So here we will be needing two agents.",
                    "start_time": 1877.64,
                    "end_time": 1880.2
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "One for indexing the document and the second agent will be updated for this like for analyzing and like for executing the stress test.",
                    "start_time": 1880.2,
                    "end_time": 1891.96
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So x second, there one more thing in the second approach which I need to mention 1 second.",
                    "start_time": 1892.6,
                    "end_time": 1901.33
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Picture.",
                    "start_time": 1906.85,
                    "end_time": 1907.49
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah.",
                    "start_time": 1907.73,
                    "end_time": 1908.21
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So in the like while when we start when we will implement the second approach, first we will go with the single agent approach.",
                    "start_time": 1910.29,
                    "end_time": 1919.65
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like if the single agent is enough to implement the stress test on his own, then we will like stay with the single agent.",
                    "start_time": 1919.65,
                    "end_time": 1927.21
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Else we will again like move to a multi agent architecture in the answer generation pipeline.",
                    "start_time": 1927.21,
                    "end_time": 1934.25
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So there will be a primary agent which act as a supervisor agent which handle the query.",
                    "start_time": 1934.65,
                    "end_time": 1940.57
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "If if the query is general or delegate the query it's regarding the stress test.",
                    "start_time": 1941.05,
                    "end_time": 1945.49
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And then specialized agent will be made for executing a stress test only.",
                    "start_time": 1945.49,
                    "end_time": 1950.41
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So this is the second approach.",
                    "start_time": 1951.69,
                    "end_time": 1954.09
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Is there a third agent who does a validation of the simulation analysis.",
                    "start_time": 1959.38,
                    "end_time": 1968.9
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So the second region does it as a preparer as a reviewer who also reviews the output and validates it.",
                    "start_time": 1969.54,
                    "end_time": 1976.18
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, so the primary agent provides secondary agent the function of the stress test simulation.",
                    "start_time": 1977.78,
                    "end_time": 1987.76
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then the second agent is responsible for get gathering the data, validating the data and generating the output and validating the same.",
                    "start_time": 1987.92,
                    "end_time": 1995.2
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah,",
                    "start_time": 1996.32,
                    "end_time": 1996.8
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So the second reaction is validating the work is prepared is what you're saying.",
                    "start_time": 2002.88,
                    "end_time": 2007.2
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, simulation result will be validated by the second agent.",
                    "start_time": 2008.33,
                    "end_time": 2011.69
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like yeah, if we move to like multi agent architecture.",
                    "start_time": 2011.93,
                    "end_time": 2017.01
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "If the single agent is enough like if we get good accuracy with single agent then we will stay with the single agent architecture as we are already doing.",
                    "start_time": 2017.01,
                    "end_time": 2025.29
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So like should I show a demo of this approach or you have any question regarding the like how it is being implemented?",
                    "start_time": 2031.93,
                    "end_time": 2039.75
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We can show the demo first, then we can take up the questions.",
                    "start_time": 2045.51,
                    "end_time": 2048.95
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 2049.19,
                    "end_time": 2049.67
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 2049.67,
                    "end_time": 2050.15
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So like this is a.",
                    "start_time": 2055.83,
                    "end_time": 2057.27
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "This is Langsmith platform for like testing the agent rapidly.",
                    "start_time": 2057.59,
                    "end_time": 2063.99
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So I built the POC regarding the approach to.",
                    "start_time": 2063.99,
                    "end_time": 2067.75
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So I will be showing you a demo of that POC using this platform.",
                    "start_time": 2068.07,
                    "end_time": 2073.11
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So I'm.",
                    "start_time": 2074.39,
                    "end_time": 2075.59
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "I will stay.",
                    "start_time": 2075.59,
                    "end_time": 2076.31
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "I will be again executing this stress test.",
                    "start_time": 2076.39,
                    "end_time": 2079.99
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Queries.",
                    "start_time": 2085.99,
                    "end_time": 2086.71
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So this is the query if the market divs and we miss the revenue and this is the company ID and user ID for that.",
                    "start_time": 2091.679,
                    "end_time": 2099.039
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "We'll be automating that when we move to production.",
                    "start_time": 2099.199,
                    "end_time": 2101.999
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "For now we are providing it in the query.",
                    "start_time": 2102.079,
                    "end_time": 2104.079
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So agent will hit the query.",
                    "start_time": 2105.279,
                    "end_time": 2108.719
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So first it retrieved the document from the vector database and retrieve the function to execute the stress test.",
                    "start_time": 2110.639,
                    "end_time": 2119.93
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Now it will go ahead and start gathering the data required to execute that stress test.",
                    "start_time": 2124.17,
                    "end_time": 2130.41
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "It passed opening cash balance and one rate it is getting monthly revenue OPEX and capex.",
                    "start_time": 2137.45,
                    "end_time": 2144.74
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, forecasted data is here now.",
                    "start_time": 2146.82,
                    "end_time": 2148.82
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Revenue for.",
                    "start_time": 2154.5,
                    "end_time": 2155.46
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, So when all the input are fetched from the database then it it use and tool prepared to execute the stress test.",
                    "start_time": 2185.87,
                    "end_time": 2199.34
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So that tool required the simulation function for stress test and the input which is gathered from the database then execute them on the stress test then return the output.",
                    "start_time": 2199.9,
                    "end_time": 2215.34
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So as of now I think there's a.",
                    "start_time": 2216.22,
                    "end_time": 2219.74
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "There's an issue in the function that's why is returning insolvent.",
                    "start_time": 2219.82,
                    "end_time": 2224.64
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "But yeah means it can be executed in this way also.",
                    "start_time": 2224.72,
                    "end_time": 2229.76
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So when inputs are gathered it will be passed on to the function dynamically and the output generated by function will be returned and it will be shown to the user in proper way as we are showing here like in the form of graph and the summarization and other things.",
                    "start_time": 2229.92,
                    "end_time": 2245.44
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So for now it returning this with the four months.",
                    "start_time": 2248.01,
                    "end_time": 2253.85
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Under this condition your cash balance will fall below the minimum required cash of this within next moment.",
                    "start_time": 2255.77,
                    "end_time": 2263.49
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "This means under these condition your cash variant Will fall below the minimum distance.",
                    "start_time": 2263.49,
                    "end_time": 2268.49
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So the purpose of this POC was like examining that we can execute the stress test dynamically or not.",
                    "start_time": 2272.34,
                    "end_time": 2280.3
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So it is possible like after doing the poc.",
                    "start_time": 2280.3,
                    "end_time": 2283.94
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Harsh.",
                    "start_time": 2285.38,
                    "end_time": 2286.02
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Is there any like.",
                    "start_time": 2286.1,
                    "end_time": 2287.38
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Is there proper output?",
                    "start_time": 2288.82,
                    "end_time": 2290.1
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Have you ever.",
                    "start_time": 2290.1,
                    "end_time": 2290.82
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "If there is improper output of previously which you have run, can you showcase that?",
                    "start_time": 2291.46,
                    "end_time": 2295.22
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "I need to look into that.",
                    "start_time": 2296.74,
                    "end_time": 2298.34
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Did I have that?",
                    "start_time": 2302.56,
                    "end_time": 2303.6
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So what I believe you said in the previous approach there will be unit test cases.",
                    "start_time": 2324.49,
                    "end_time": 2329.61
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "All of that will be part of pipeline and that requires more effort in terms of validating and it.",
                    "start_time": 2330.33,
                    "end_time": 2339.13
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "It has a deterministic output.",
                    "start_time": 2339.13,
                    "end_time": 2341.85
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Based on your initial testing, what I would say what.",
                    "start_time": 2342.25,
                    "end_time": 2349.53
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What made you feel that this is a better approach in terms of solving a same problem?",
                    "start_time": 2350.1,
                    "end_time": 2356.02
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "In terms.",
                    "start_time": 2358.82,
                    "end_time": 2359.38
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "In terms of solving what?",
                    "start_time": 2359.46,
                    "end_time": 2360.82
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "See same situation.",
                    "start_time": 2361.94,
                    "end_time": 2363.94
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Right.",
                    "start_time": 2363.94,
                    "end_time": 2364.34
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "You felt that this is a.",
                    "start_time": 2364.42,
                    "end_time": 2366.179
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "This is an agentic approach.",
                    "start_time": 2366.26,
                    "end_time": 2367.62
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "But it.",
                    "start_time": 2368.1,
                    "end_time": 2370.1
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What.",
                    "start_time": 2370.18,
                    "end_time": 2370.58
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What extra you get with this approach?",
                    "start_time": 2370.82,
                    "end_time": 2373.14
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Right?",
                    "start_time": 2373.22,
                    "end_time": 2373.58
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's.",
                    "start_time": 2373.58,
                    "end_time": 2374.06
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's documenting.",
                    "start_time": 2374.06,
                    "end_time": 2375.3
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So parsing from document is one, what's another?",
                    "start_time": 2376.75,
                    "end_time": 2380.03
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay, so previously defining a deterministic flow in code that's one piece you need to do it from a markdown document.",
                    "start_time": 2380.27,
                    "end_time": 2389.63
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's one difference.",
                    "start_time": 2390.83,
                    "end_time": 2391.989
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What I feel in a functional building up what others.",
                    "start_time": 2391.989,
                    "end_time": 2395.55
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay, so another could be just helping you out.",
                    "start_time": 2397.31,
                    "end_time": 2401.31
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Another could be.",
                    "start_time": 2401.64,
                    "end_time": 2402.44
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "This is a multi agent flow and that's a single agent managing everything.",
                    "start_time": 2402.84,
                    "end_time": 2406.44
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So what all think you feel?",
                    "start_time": 2408.04,
                    "end_time": 2410.28
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "The other thing here which is changed is we are like getting stress test function from the vector database.",
                    "start_time": 2411.72,
                    "end_time": 2419.88
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we were like previously we were routing it into our code, but now we are getting that from the vector database and we are executing it into the flow itself.",
                    "start_time": 2420.2,
                    "end_time": 2432.02
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That needs to be part of vector or is just.",
                    "start_time": 2433.7,
                    "end_time": 2436.02
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "This can just be part of your lang graph node and subgraphs also you can manage that from subgraphs also your deterministic flow.",
                    "start_time": 2436.02,
                    "end_time": 2444.5
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Right,",
                    "start_time": 2445.54,
                    "end_time": 2445.94
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "we can manage that.",
                    "start_time": 2447.94,
                    "end_time": 2449.74
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "But again for classification we need like.",
                    "start_time": 2449.74,
                    "end_time": 2453.34
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "We need what?",
                    "start_time": 2453.34,
                    "end_time": 2454.42
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So how we will classify the query then?",
                    "start_time": 2455.07,
                    "end_time": 2457.19
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like can I.",
                    "start_time": 2457.19,
                    "end_time": 2458.31
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Can I.",
                    "start_time": 2458.31,
                    "end_time": 2458.75
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Since you have filled in, can I look into a document which you prompted as a. I would say for embedding into a chunk date and then you push into PG vector.",
                    "start_time": 2458.91,
                    "end_time": 2471.91
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What is the document?",
                    "start_time": 2471.91,
                    "end_time": 2472.63
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Are you looking at?",
                    "start_time": 2472.63,
                    "end_time": 2473.47
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, which document?",
                    "start_time": 2475.87,
                    "end_time": 2477.43
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "You are like here the status quo document which you fed into the vector db.",
                    "start_time": 2477.43,
                    "end_time": 2482.32
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, one second.",
                    "start_time": 2483.52,
                    "end_time": 2484.48
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "You are talking about the flow.",
                    "start_time": 2484.8,
                    "end_time": 2486.24
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yes.",
                    "start_time": 2487.28,
                    "end_time": 2487.76
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Your first step is you have a set of documents which have let's say a set of stress tests.",
                    "start_time": 2488.48,
                    "end_time": 2495.4
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I want to look at what.",
                    "start_time": 2495.4,
                    "end_time": 2496.48
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What was the first step?",
                    "start_time": 2497.12,
                    "end_time": 2498.56
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Which document?",
                    "start_time": 2498.64,
                    "end_time": 2499.6
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "How the document.",
                    "start_time": 2499.68,
                    "end_time": 2500.52
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Let's say it was on docx.",
                    "start_time": 2500.52,
                    "end_time": 2501.68
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I will want to look into the docx Document.",
                    "start_time": 2501.68,
                    "end_time": 2504.08
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, okay, So give me a second.",
                    "start_time": 2504.72,
                    "end_time": 2512.33
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "This is just like sample we referred to while creating the function for the four vector database.",
                    "start_time": 2517.93,
                    "end_time": 2525.29
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So you got this document from like",
                    "start_time": 2526.81,
                    "end_time": 2531.05
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "we created this document on our own.",
                    "start_time": 2531.29,
                    "end_time": 2534.25
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, yeah.",
                    "start_time": 2535.45,
                    "end_time": 2536.73
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Then after that like we just give this document to the to LLM and that just created strategy.",
                    "start_time": 2537.13,
                    "end_time": 2547.21
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So what is the stocking strategy?",
                    "start_time": 2547.21,
                    "end_time": 2549.69
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "What is chunking strategy?",
                    "start_time": 2550.17,
                    "end_time": 2552.33
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "How did you bifurcated this logic?",
                    "start_time": 2553.93,
                    "end_time": 2555.73
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, yeah.",
                    "start_time": 2555.73,
                    "end_time": 2556.25
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So.",
                    "start_time": 2558.97,
                    "end_time": 2559.37
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Oh no, yeah, that part is for like first agent which.",
                    "start_time": 2560.26,
                    "end_time": 2564.98
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Which will like convert documented to markdown and like write the function for it.",
                    "start_time": 2564.98,
                    "end_time": 2570.42
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "For the POC purpose we just like give this document to the LLM and created a concise function which is including all the logic just for like like looking like feasibility purpose.",
                    "start_time": 2570.74,
                    "end_time": 2587.92
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like if it is possible not.",
                    "start_time": 2587.92,
                    "end_time": 2589.24
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "But yeah, we can also convert it using agent as well.",
                    "start_time": 2589.24,
                    "end_time": 2596.16
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "My point here is we didn't like write the agent to convert this document in the Python function for now we just created a sample function for that that is not done yet.",
                    "start_time": 2598.32,
                    "end_time": 2610.88
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Just a point.",
                    "start_time": 2614.97,
                    "end_time": 2615.61
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Ashby, this was on the motivation of you said that you wanted.",
                    "start_time": 2615.61,
                    "end_time": 2619.61
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I do understand.",
                    "start_time": 2620.25,
                    "end_time": 2621.05
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "But you want to understand.",
                    "start_time": 2621.05,
                    "end_time": 2622.41
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "See, see for me the document.",
                    "start_time": 2622.49,
                    "end_time": 2624.97
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So if that this document is going to be part of my general let's say flow I need to understand what is the document about.",
                    "start_time": 2625.29,
                    "end_time": 2633.41
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 2633.41,
                    "end_time": 2633.85
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "How they have chunked so they have reached to a success story around it.",
                    "start_time": 2633.85,
                    "end_time": 2637.61
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "See, that's important because.",
                    "start_time": 2638.32,
                    "end_time": 2639.92
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Because I need to follow the same strategy of building a document.",
                    "start_time": 2640.48,
                    "end_time": 2644
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Right.",
                    "start_time": 2644.4,
                    "end_time": 2644.8
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's the simple garbage in, garbage out.",
                    "start_time": 2645.04,
                    "end_time": 2647.64
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "If there is something that Harsh will identify will give you a template that we think that works.",
                    "start_time": 2647.64,
                    "end_time": 2654.32
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah.",
                    "start_time": 2655.68,
                    "end_time": 2656.16
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Happen based on",
                    "start_time": 2657.04,
                    "end_time": 2658.08
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "processes.",
                    "start_time": 2660.48,
                    "end_time": 2661.2
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "For now you just give this document to lm.",
                    "start_time": 2661.28,
                    "end_time": 2664.48
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay, that was just",
                    "start_time": 2665.04,
                    "end_time": 2666.56
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "so like I have already implemented recession Playbook.",
                    "start_time": 2668.88,
                    "end_time": 2672.72
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "This would give you a better output than the deterministic one.",
                    "start_time": 2673.84,
                    "end_time": 2677.2
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Actually output will will be same because we will be validating it before like indexing that function into the vector database so the output will be the same like in both cases.",
                    "start_time": 2679.2,
                    "end_time": 2692.09
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "And I think Harsh has concluded that the output both from either approaches was the same.",
                    "start_time": 2694.57,
                    "end_time": 2700.25
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "It's just a convenience in the document ingestion phase that you get here.",
                    "start_time": 2700.49,
                    "end_time": 2704.25
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I could see There was a 30 seconds latency in the previous one.",
                    "start_time": 2704.81,
                    "end_time": 2708.81
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Any.",
                    "start_time": 2708.89,
                    "end_time": 2709.25
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Any add on to this approach or it will reduce that thought.",
                    "start_time": 2709.25,
                    "end_time": 2712.57
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What is in in general without using any caching or any other reducing latency technique.",
                    "start_time": 2712.65,
                    "end_time": 2719.53
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What is the Apple to Apple comparison in between both of them?",
                    "start_time": 2719.53,
                    "end_time": 2723.57
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So like for the second approach currently it is taking around 60 seconds in POC.",
                    "start_time": 2724.53,
                    "end_time": 2732.13
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So it is almost double like.",
                    "start_time": 2732.85,
                    "end_time": 2734.53
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah.",
                    "start_time": 2734.77,
                    "end_time": 2735.25
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "And token utilization would also be double in the Agent, right?",
                    "start_time": 2737.17,
                    "end_time": 2742.42
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, right.",
                    "start_time": 2742.74,
                    "end_time": 2743.38
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "It is.",
                    "start_time": 2743.38,
                    "end_time": 2743.78
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah it almost earlier.",
                    "start_time": 2743.78,
                    "end_time": 2745.62
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "I have also written",
                    "start_time": 2751.7,
                    "end_time": 2752.9
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "optimization or once you've optimized the flows beyond poc, what would.",
                    "start_time": 2755.3,
                    "end_time": 2761.14
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "What would you expect?",
                    "start_time": 2761.38,
                    "end_time": 2762.26
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "A realistic.",
                    "start_time": 2763.7,
                    "end_time": 2764.66
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "I can like after optimization latency will definitely be decreased but how much it will decrease that will depend like 10 second delay can be easily done like around 50 seconds it can be like executed but after 50 seconds like we need to see like based on the optimizations and the token utilization will also be less like we can also include like cheaper models for like steps which don't need so much intelligence.",
                    "start_time": 2767.63,
                    "end_time": 2800.76
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Which model you were using as of now for POC?",
                    "start_time": 2800.84,
                    "end_time": 2804.24
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "For both of them?",
                    "start_time": 2804.24,
                    "end_time": 2805.16
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Gemini 2.5 flash.",
                    "start_time": 2807.4,
                    "end_time": 2809.08
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "It's a fast model.",
                    "start_time": 2810.2,
                    "end_time": 2811.4
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, it's a fast model.",
                    "start_time": 2811.88,
                    "end_time": 2813.48
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So you don't need any.",
                    "start_time": 2814.6,
                    "end_time": 2816.04
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I don't think so you need any thinking model even for multi agent also.",
                    "start_time": 2816.92,
                    "end_time": 2821.49
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, but like I experimented with Gemin Gemini 2.5 flashlight.",
                    "start_time": 2824.69,
                    "end_time": 2831.81
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So for with that responses were fast but they were not that much accurate.",
                    "start_time": 2832.05,
                    "end_time": 2837.13
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So a little bit of experimentation needed here.",
                    "start_time": 2837.13,
                    "end_time": 2840.05
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "But in terms of.",
                    "start_time": 2840.05,
                    "end_time": 2842.69
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "When you say it was not accurate what that's.",
                    "start_time": 2844.53,
                    "end_time": 2846.69
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Can you be bit specific?",
                    "start_time": 2847.31,
                    "end_time": 2848.75
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "It was not giving right numbers.",
                    "start_time": 2848.75,
                    "end_time": 2849.95
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "It was not able to summarize better",
                    "start_time": 2849.95,
                    "end_time": 2852.11
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "so it was not able to like form the SQL queries properly rest it was doing good but in case of SQL query formation it was not good.",
                    "start_time": 2852.75,
                    "end_time": 2862.91
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So.",
                    "start_time": 2866.35,
                    "end_time": 2866.67
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah.",
                    "start_time": 2866.67,
                    "end_time": 2867.07
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "And by the way did you get a chance where I have suggested flow four agents in the multi agent.",
                    "start_time": 2867.31,
                    "end_time": 2875.56
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Did you get a chance to look into it?",
                    "start_time": 2875.56,
                    "end_time": 2877.4
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So I. I don't remember like when did you suggest it?",
                    "start_time": 2881.08,
                    "end_time": 2887.24
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "No worries, no worries.",
                    "start_time": 2888.519,
                    "end_time": 2889.52
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I have.",
                    "start_time": 2889.52,
                    "end_time": 2889.96
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I'm just sharing a document here Again I've also commented you so I believe that will add more.",
                    "start_time": 2889.96,
                    "end_time": 2897.24
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 2899.49,
                    "end_time": 2899.97
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "More complexity and will need more.",
                    "start_time": 2900.13,
                    "end_time": 2902.93
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 2902.93,
                    "end_time": 2903.49
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay, let me.",
                    "start_time": 2903.57,
                    "end_time": 2904.45
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, you are presenting.",
                    "start_time": 2905.81,
                    "end_time": 2907.17
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "No, no, I'm just shared the document.",
                    "start_time": 2907.49,
                    "end_time": 2909.25
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I am it's just that validation one which also said.",
                    "start_time": 2909.41,
                    "end_time": 2914.81
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "And second I'm saying one two just pull in the data it's it so one supervisor who understands the routes based on intent and requirement.",
                    "start_time": 2914.81,
                    "end_time": 2927.23
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah, just four of the things anyways you can look into it.",
                    "start_time": 2927.23,
                    "end_time": 2930.03
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay.",
                    "start_time": 2930.03,
                    "end_time": 2930.71
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "For the question we can do one thing.",
                    "start_time": 2932.63,
                    "end_time": 2935.75
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We can share you like for the session playbook only we can share you everything in detail.",
                    "start_time": 2935.91,
                    "end_time": 2941.07
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like how we are getting the values and what are the like different possibilities where like agent is looking into and what is like then a response that is returning.",
                    "start_time": 2941.07,
                    "end_time": 2951.91
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So you can also look into it how we are calculating and you can check all the steps in detail and if you find anything concerning you can let us know.",
                    "start_time": 2952.19,
                    "end_time": 2959.55
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Have you Planned out how your let's say I've given you four agents plan planner out how you will work with sub graphs and graphs and nodes and tools in each agents based on their role.",
                    "start_time": 2960.19,
                    "end_time": 2974.59
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "And yeah you try to create a lang graph and identify how will you solve it.",
                    "start_time": 2975.31,
                    "end_time": 2984.63
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "And let's.",
                    "start_time": 2985.51,
                    "end_time": 2986.47
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Let's come back on the design then.",
                    "start_time": 2986.47,
                    "end_time": 2988.31
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 2991.43,
                    "end_time": 2992.07
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "So Ashpreet, you.",
                    "start_time": 3006.72,
                    "end_time": 3007.68
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "You'd want to see that design before you make a decision, right?",
                    "start_time": 3007.68,
                    "end_time": 3010.72
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah because what I feel I'm still not confident with the output received in the deterministic flow approach one that's.",
                    "start_time": 3011.92,
                    "end_time": 3020.08
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's what he feels it's.",
                    "start_time": 3020.08,
                    "end_time": 3022.96
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Maybe it might require more testing or",
                    "start_time": 3023.44,
                    "end_time": 3026.68
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "more",
                    "start_time": 3026.68,
                    "end_time": 3027.04
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I would say validation.",
                    "start_time": 3029.13,
                    "end_time": 3030.33
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "All of that.",
                    "start_time": 3030.49,
                    "end_time": 3031.21
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah but if we need to go into the approach to then we have",
                    "start_time": 3031.37,
                    "end_time": 3035.81
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "to be pretty",
                    "start_time": 3035.81,
                    "end_time": 3036.49
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "solid in our design.",
                    "start_time": 3038.33,
                    "end_time": 3039.69
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So when we start implementing it should solve it because based on the document if document is not well articulated or given to the vector I embedded correctly it will still have the same issue of and getting into it.",
                    "start_time": 3039.85,
                    "end_time": 3059.59
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I just want to solve that problem as well.",
                    "start_time": 3059.59,
                    "end_time": 3061.55
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "If you're going to that approach.",
                    "start_time": 3061.55,
                    "end_time": 3062.99
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "If we are going to that approach.",
                    "start_time": 3062.99,
                    "end_time": 3064.35
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay.",
                    "start_time": 3064.35,
                    "end_time": 3064.87
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "How better refined because let's say he says three days of effort in.",
                    "start_time": 3067.03,
                    "end_time": 3072.23
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "In this deterministic can we into one effort adding another another stress test with this current approach.",
                    "start_time": 3072.23,
                    "end_time": 3084.48
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "If that saves me time and effort and make that production ready in within one day.",
                    "start_time": 3084.8,
                    "end_time": 3089.88
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's.",
                    "start_time": 3089.88,
                    "end_time": 3090.32
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's the benefit.",
                    "start_time": 3090.32,
                    "end_time": 3091.08
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I get it with the new approach and I can take a better decision.",
                    "start_time": 3091.08,
                    "end_time": 3095.04
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I hope that sounds well to you Akash.",
                    "start_time": 3095.36,
                    "end_time": 3097.84
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "It makes sense.",
                    "start_time": 3100.96,
                    "end_time": 3101.84
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 3102.32,
                    "end_time": 3102.8
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "So if I could suggest that we the comparison pros and cons part that you had in the document if you can expand that out to include more detail around once you've optimized what we can achieve on both approaches in terms of setting up a new stress test latencies included the tokenization and all the details that will help them.",
                    "start_time": 3103.28,
                    "end_time": 3129.91
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "If there's anything else I should be up missing let me know.",
                    "start_time": 3129.91,
                    "end_time": 3132.07
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "But if we can summarize that one place that I think would be useful as well.",
                    "start_time": 3132.07,
                    "end_time": 3137.3
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 3137.54,
                    "end_time": 3138.1
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "All right.",
                    "start_time": 3139.06,
                    "end_time": 3139.62
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "And sorry one more thing.",
                    "start_time": 3142.02,
                    "end_time": 3143.98
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "There are some feedbacks on Unified Document and have some feedbacks in this document.",
                    "start_time": 3143.98,
                    "end_time": 3149.34
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I just want if you can combine that or put everything on one page so it helps for module four.",
                    "start_time": 3149.34,
                    "end_time": 3155.94
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Akash,",
                    "start_time": 3156.18,
                    "end_time": 3156.82
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "so you've sent some stuff to us and you want it consolidated in that unified scope.",
                    "start_time": 3160.58,
                    "end_time": 3165.07
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, so I have.",
                    "start_time": 3165.22,
                    "end_time": 3166.34
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I've given feedback to both of the pages.",
                    "start_time": 3166.5,
                    "end_time": 3168.5
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So there was some bit of information on Unifieds and some of bit of this new AI architecture one so you can Just correlate and put it together.",
                    "start_time": 3168.82,
                    "end_time": 3179.54
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That helps you as a feedback also so you can work on just, just whatever sounds better to you so you don't miss any feedback.",
                    "start_time": 3179.54,
                    "end_time": 3188.9
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Just that.",
                    "start_time": 3188.98,
                    "end_time": 3190.42
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Okay, so Simran, let us know if you guys have access to the documents first and then if you could do it and then give us your feedback and then we can decide how we want to combine it onto the document.",
                    "start_time": 3192.11,
                    "end_time": 3203.79
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Sure.",
                    "start_time": 3204.51,
                    "end_time": 3204.87
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "I'll check the assess and then we will look into it that the feedback that he provided on both of the features and then we can consolidate that and can work accordingly and then we can start with the design part that he requested for.",
                    "start_time": 3204.87,
                    "end_time": 3217.36
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Okay, thank you.",
                    "start_time": 3221.68,
                    "end_time": 3222.88
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "I know it's hard to predict how long this activity and preparation will take, but roughly are you guys in a position to suggest now or would you need, you know, you can take some time after this call to let us know.",
                    "start_time": 3223.52,
                    "end_time": 3237.2
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We need some time to look into it and then we can provide you with the estimated time that how this effort will require Time.",
                    "start_time": 3238.08,
                    "end_time": 3245.05
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Yeah, sure.",
                    "start_time": 3247.77,
                    "end_time": 3248.45
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "If you could let us know so we can let Katie team know.",
                    "start_time": 3248.45,
                    "end_time": 3251.57
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah, I'll ping you.",
                    "start_time": 3251.57,
                    "end_time": 3252.57
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So regarding the efforts or regarding how much time that we require to do all these things and when we can showcase you something",
                    "start_time": 3252.57,
                    "end_time": 3259.53
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "I have, I have some question to Ashweet.",
                    "start_time": 3261.69,
                    "end_time": 3264.89
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 3265.37,
                    "end_time": 3265.93
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yes.",
                    "start_time": 3266.33,
                    "end_time": 3266.81
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So when you were asking about chunking so you are asking like how we are storing it into the vector database or how we we are converting the document into the function.",
                    "start_time": 3267.77,
                    "end_time": 3277.59
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Like I, I didn't get it storing into vector database.",
                    "start_time": 3277.59,
                    "end_time": 3282.55
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So you, so let's say you cannot chunk the complete document into one or, or you can identify.",
                    "start_time": 3282.79,
                    "end_time": 3290.47
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay, this is the fun vector.",
                    "start_time": 3290.47,
                    "end_time": 3292.55
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "How do you want to solve it?",
                    "start_time": 3292.55,
                    "end_time": 3294.11
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Because it's a, it's a problem then has a solution.",
                    "start_time": 3294.11,
                    "end_time": 3297.19
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "But it's a, but solution is a big document.",
                    "start_time": 3297.51,
                    "end_time": 3299.79
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What I see it's a two page document.",
                    "start_time": 3299.79,
                    "end_time": 3301.59
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay so like I can answer this question like so yes I can.",
                    "start_time": 3301.84,
                    "end_time": 3306.8
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So, so, so the, the document.",
                    "start_time": 3316.88,
                    "end_time": 3324.64
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah.",
                    "start_time": 3325.76,
                    "end_time": 3326.2
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So the second approach, in the second approach the agent will generate a concise summary of the whole document and a Python function which like contain the simulation logic and provide output.",
                    "start_time": 3326.2,
                    "end_time": 3339
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So what we are doing here is we are generating embeddings of the summary which was provided regarding that stress test.",
                    "start_time": 3339.48,
                    "end_time": 3349
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And so when the query will come the similarity search will be like based on the summary and the output which will be given after that search is the executable function.",
                    "start_time": 3349.48,
                    "end_time": 3360.84
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So it's a kind of parent document retriever.",
                    "start_time": 3360.84,
                    "end_time": 3363.44
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we will apply search on the summary and the output will be the stress test function.",
                    "start_time": 3364.08,
                    "end_time": 3369.2
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we are not like embedding the whole document or this.",
                    "start_time": 3369.2,
                    "end_time": 3371.92
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "We are just embedding the summary of the document like this much only.",
                    "start_time": 3372,
                    "end_time": 3375.68
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay.",
                    "start_time": 3378.96,
                    "end_time": 3379.48
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "And what is the retrieval strategy?",
                    "start_time": 3379.48,
                    "end_time": 3381.52
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "It is.",
                    "start_time": 3381.52,
                    "end_time": 3382
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Since I can see you have added metadata.",
                    "start_time": 3382.08,
                    "end_time": 3384.56
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah.",
                    "start_time": 3384.64,
                    "end_time": 3385
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So you.",
                    "start_time": 3385,
                    "end_time": 3385.44
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "You're providing as a metadata.",
                    "start_time": 3385.68,
                    "end_time": 3387.36
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "How do you searching from.",
                    "start_time": 3387.36,
                    "end_time": 3388.97
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "From the vector.",
                    "start_time": 3389.29,
                    "end_time": 3390.25
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So we are searching based on query and.",
                    "start_time": 3390.65,
                    "end_time": 3393.45
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "And the output is metadata.",
                    "start_time": 3393.61,
                    "end_time": 3395.69
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like in the output we are getting the three field from the metadata.",
                    "start_time": 3395.69,
                    "end_time": 3399.05
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "That is entry point and the function which is need to be executed.",
                    "start_time": 3399.21,
                    "end_time": 3403.37
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "It's just a semantic search.",
                    "start_time": 3403.77,
                    "end_time": 3405.61
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, it's a semantic search.",
                    "start_time": 3407.21,
                    "end_time": 3408.89
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah.",
                    "start_time": 3409.29,
                    "end_time": 3409.77
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Okay, so I will suggest you since you have a metadata also I will suggest you use a semantic search kind of in a hybrid search semantic plus and metadata.",
                    "start_time": 3410.01,
                    "end_time": 3418.86
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Because you're using metadata also attack.",
                    "start_time": 3418.86,
                    "end_time": 3420.86
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So that will fast your help you to your query will be faster and more try that approach.",
                    "start_time": 3421.18,
                    "end_time": 3429.5
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Yeah, I I will look into that also.",
                    "start_time": 3429.74,
                    "end_time": 3431.54
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like if it makes it more accurate and fast, then we will surely do that.",
                    "start_time": 3431.54,
                    "end_time": 3435.34
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "We can do that.",
                    "start_time": 3435.5,
                    "end_time": 3436.38
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah, because you are already.",
                    "start_time": 3437.02,
                    "end_time": 3439.1
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Because during your chunking you're storing as a metadata as well and summary as well.",
                    "start_time": 3439.26,
                    "end_time": 3443.78
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Because okay, so during your retrieval you if you do this it will faster query will be faster.",
                    "start_time": 3443.78,
                    "end_time": 3449.36
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, I will look into that.",
                    "start_time": 3452,
                    "end_time": 3453.6
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Oh and and the second question is the document you provided where four agent are mentioned.",
                    "start_time": 3454.8,
                    "end_time": 3460.96
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So regarding that you are saying that go through that document and like what's",
                    "start_time": 3461.28,
                    "end_time": 3466.76
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "your thought around that?",
                    "start_time": 3466.76,
                    "end_time": 3467.68
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So like and then come up with like optimized approach.",
                    "start_time": 3468.24,
                    "end_time": 3471.86
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like it's a optimized version of the approach too.",
                    "start_time": 3471.86,
                    "end_time": 3474.9
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Am I correct here?",
                    "start_time": 3474.9,
                    "end_time": 3475.94
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yes.",
                    "start_time": 3476.18,
                    "end_time": 3476.66
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yes.",
                    "start_time": 3476.66,
                    "end_time": 3477.14
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay.",
                    "start_time": 3478.42,
                    "end_time": 3479.06
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So you are asking like how will we can implement it?",
                    "start_time": 3479.22,
                    "end_time": 3483.02
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like how much time it will take and all other things regarding that.",
                    "start_time": 3483.02,
                    "end_time": 3486.34
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yes, yes.",
                    "start_time": 3486.66,
                    "end_time": 3487.86
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "And other than that like you want the like feedback on.",
                    "start_time": 3488.42,
                    "end_time": 3491.86
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "On your points which are like the feedback which you gave us.",
                    "start_time": 3491.86,
                    "end_time": 3494.42
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like we need to.",
                    "start_time": 3494.42,
                    "end_time": 3495.46
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We need to give a thinking on that too.",
                    "start_time": 3495.7,
                    "end_time": 3497.7
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Back on my point.",
                    "start_time": 3499.16,
                    "end_time": 3499.84
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I'm just looking take that in your account and think how you design it.",
                    "start_time": 3499.84,
                    "end_time": 3503.56
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 3503.8,
                    "end_time": 3504.32
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Actually we have replied to some of your queries yesterday.",
                    "start_time": 3504.32,
                    "end_time": 3507.48
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "If you have like if you want like we can do it now.",
                    "start_time": 3508.28,
                    "end_time": 3511.04
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Otherwise we can take up it like next time.",
                    "start_time": 3511.04,
                    "end_time": 3513.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 3514.6,
                    "end_time": 3515
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "If you have any.",
                    "start_time": 3515,
                    "end_time": 3515.8
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I could see he said we are already it's in high level one.",
                    "start_time": 3516.6,
                    "end_time": 3520.28
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "We have taken care of the feedbacks.",
                    "start_time": 3520.52,
                    "end_time": 3522.2
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's fine.",
                    "start_time": 3522.2,
                    "end_time": 3522.52
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's fine.",
                    "start_time": 3522.52,
                    "end_time": 3523.08
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I understand.",
                    "start_time": 3523.91,
                    "end_time": 3524.39
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "If you've already taken care, that's good.",
                    "start_time": 3525.03,
                    "end_time": 3526.75
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "If not take care.",
                    "start_time": 3526.75,
                    "end_time": 3528.07
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's one in approach to.",
                    "start_time": 3528.07,
                    "end_time": 3530.31
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Maybe their feedback is not missed on is missing because that was in a different unified scope document your feedbacks are 1 on AI Architecture Diagram 1.",
                    "start_time": 3530.39,
                    "end_time": 3540.79
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "That's right.",
                    "start_time": 3540.79,
                    "end_time": 3541.35
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I have defined agents definitions there because previous year also mentioned previous ones there.",
                    "start_time": 3544.39,
                    "end_time": 3551.28
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Just look into that input document.",
                    "start_time": 3551.28,
                    "end_time": 3553.28
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay, sure.",
                    "start_time": 3553.84,
                    "end_time": 3554.64
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "And we need to provide with the design as well.",
                    "start_time": 3557.2,
                    "end_time": 3559.44
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 3560.56,
                    "end_time": 3561.04
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I'm saying think about how you better design it.",
                    "start_time": 3561.2,
                    "end_time": 3565.2
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So it helped me as an user or also as a client.",
                    "start_time": 3565.359,
                    "end_time": 3570.4
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Let's say if you're.",
                    "start_time": 3570.64,
                    "end_time": 3571.6
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "If three days has been taken can we optimize do a one day production ready deployment.",
                    "start_time": 3571.6,
                    "end_time": 3576.72
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's what I will say.",
                    "start_time": 3577.62,
                    "end_time": 3578.7
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "If effort right.",
                    "start_time": 3578.7,
                    "end_time": 3579.86
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "That's when then I will be able to take a better decision also got your point.",
                    "start_time": 3579.94,
                    "end_time": 3585.38
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 3585.46,
                    "end_time": 3586.02
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "So on the whole you need an optimized version of approach two.",
                    "start_time": 3588.1,
                    "end_time": 3592.5
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yes.",
                    "start_time": 3593.86,
                    "end_time": 3594.34
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes.",
                    "start_time": 3594.58,
                    "end_time": 3595.06
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay.",
                    "start_time": 3595.06,
                    "end_time": 3595.7
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "But three days like we said for the approach one.",
                    "start_time": 3596.18,
                    "end_time": 3599.06
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We didn't set for three days for the approach two.",
                    "start_time": 3599.06,
                    "end_time": 3601.22
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I do understand.",
                    "start_time": 3602.51,
                    "end_time": 3603.07
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "I do understand.",
                    "start_time": 3603.39,
                    "end_time": 3604.11
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So let's say.",
                    "start_time": 3604.67,
                    "end_time": 3605.47
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Let's say if you say approach to is already optimized and solved it from one day itself.",
                    "start_time": 3605.47,
                    "end_time": 3610.75
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah.",
                    "start_time": 3610.91,
                    "end_time": 3611.47
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Then it's good for me.",
                    "start_time": 3611.71,
                    "end_time": 3613.07
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 3613.23,
                    "end_time": 3613.63
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah.",
                    "start_time": 3613.63,
                    "end_time": 3613.99
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Actually Ashpreet like suppose once we goes with the approach too.",
                    "start_time": 3613.99,
                    "end_time": 3619.87
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So like only thing on your side is to do like.",
                    "start_time": 3620.27,
                    "end_time": 3623.19
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Is to like we'll share you a template of our document.",
                    "start_time": 3623.19,
                    "end_time": 3626.19
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like how you doing to define this test case?",
                    "start_time": 3626.51,
                    "end_time": 3629.07
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "You just need to upload somewhere like we'll provide you a UI over there.",
                    "start_time": 3629.07,
                    "end_time": 3632.51
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "You just need to upload it.",
                    "start_time": 3632.51,
                    "end_time": 3633.79
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Rest of the things like, like.",
                    "start_time": 3634.19,
                    "end_time": 3636.27
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like we like it's just will be done in the matter of time only like once you uploaded it like at the back end it will be stored like it will generate a summary and a metadata.",
                    "start_time": 3636.43,
                    "end_time": 3645.91
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Then it will be stored to the vector DB and then you can run a stress test case over it.",
                    "start_time": 3645.91,
                    "end_time": 3649.47
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Like it will not require so much of time.",
                    "start_time": 3649.869,
                    "end_time": 3652.15
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It will just run in 5, 10 minutes only.",
                    "start_time": 3652.15,
                    "end_time": 3654.11
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah agreed.",
                    "start_time": 3655.79,
                    "end_time": 3657.27
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Agreed.",
                    "start_time": 3657.27,
                    "end_time": 3657.79
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So based on what input I have given you based on 4 think about that perspective.",
                    "start_time": 3657.79,
                    "end_time": 3663.01
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah, yeah we'll.",
                    "start_time": 3663.09,
                    "end_time": 3663.85
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We'll give it think about that too.",
                    "start_time": 3663.85,
                    "end_time": 3665.37
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Just I was clarifying like in the approach to will not require a day also like it will be done in five, 10 minutes only.",
                    "start_time": 3665.37,
                    "end_time": 3671.33
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah, that's what I'm expecting also.",
                    "start_time": 3672.61,
                    "end_time": 3674.37
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah, yeah thank you for that clarification.",
                    "start_time": 3674.69,
                    "end_time": 3677.97
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah thank you.",
                    "start_time": 3678.69,
                    "end_time": 3679.57
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We can.",
                    "start_time": 3686.37,
                    "end_time": 3686.93
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We are good for normal.",
                    "start_time": 3687.49,
                    "end_time": 3688.45
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Yeah.",
                    "start_time": 3691.41,
                    "end_time": 3691.89
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "No, I was just going to say so thanks for the discussion.",
                    "start_time": 3694.61,
                    "end_time": 3698.45
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "We'll consolidate everything and if we can get a accurate comparison between the two so we can share as we said that'd be great.",
                    "start_time": 3698.45,
                    "end_time": 3705.57
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Nothing else from my side.",
                    "start_time": 3706.85,
                    "end_time": 3708.53
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "So I'm not sure Bhavni and Gumi anything else you want to raise on top of Ashpree mentioned.",
                    "start_time": 3708.77,
                    "end_time": 3714.64
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Or anyone else on the call.",
                    "start_time": 3721.6,
                    "end_time": 3722.96
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Any other question?",
                    "start_time": 3723.28,
                    "end_time": 3724.16
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Yes, sorry, go ahead.",
                    "start_time": 3725.28,
                    "end_time": 3726.24
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So I want to clarify one thing so the optimized approach Waspreet said basically that's fine but these are just.",
                    "start_time": 3727.04,
                    "end_time": 3733.12
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I just want to clarify from the call earlier with Raheel that Raheel also mentioned these were for the preset questions.",
                    "start_time": 3733.12,
                    "end_time": 3740.89
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Right.",
                    "start_time": 3740.89,
                    "end_time": 3741.09
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So for the normal questions there's no discussion there.",
                    "start_time": 3741.09,
                    "end_time": 3746.49
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 3746.49,
                    "end_time": 3746.77
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "It's a RAG based approach for the non preset questions I just want that clarified this call.",
                    "start_time": 3746.77,
                    "end_time": 3752.61
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Sorry, when you say preset.",
                    "start_time": 3757.65,
                    "end_time": 3759.25
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Yeah, go ahead.",
                    "start_time": 3760.21,
                    "end_time": 3760.93
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "S so for normal question if they are regarding the like the company or like the document stored in the vector database then they will be answered using the regret using the reg and if they are regarding the like formulas yeah value stored in the document for example what is the revenue of January to 26?",
                    "start_time": 3760.93,
                    "end_time": 3782.75
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So then they will be answered using the data present in the SQL database Else if the question is very general like it's a greeting or something then they will be answered directly.",
                    "start_time": 3782.91,
                    "end_time": 3793.73
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Let's say if there's any question on clarification some definitions and that's not part of let's say their learning parameters of the LLM and I have given is an FNQ format in the rag let's say just some definitions would that be able to answer without any retrieval from database?",
                    "start_time": 3795.65,
                    "end_time": 3816.85
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "No.",
                    "start_time": 3818.78,
                    "end_time": 3819.02
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Like if it is not the part of like LLM training then it there are two possibility it will hallucinate or like it will not answer.",
                    "start_time": 3819.02,
                    "end_time": 3827.26
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "So in that case like we have included in the prompt if you don't know the clear answer then I gracefully decline it or only answer if the you have the supportive documents in the vector database.",
                    "start_time": 3827.26,
                    "end_time": 3838.22
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Let's say it just asks what is Achilles?",
                    "start_time": 3838.7,
                    "end_time": 3841.1
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Okay,",
                    "start_time": 3842.54,
                    "end_time": 3843.1
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "you will not know Kleids right?",
                    "start_time": 3844.87,
                    "end_time": 3846.71
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What will the answer hallucinate?",
                    "start_time": 3846.79,
                    "end_time": 3848.67
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "What I believe",
                    "start_time": 3848.67,
                    "end_time": 3849.19
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "so like in this case it will say like I don't know like about Achilles can you like I I am not able to answer this question or something like we will show a default message or like we will suggest a question like pull up question or something like that but if the document is present in the vector database or you have loaded some FAQs or something like that it will answer",
                    "start_time": 3851.03,
                    "end_time": 3872.26
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "using them only so we expecting that to happen.",
                    "start_time": 3872.26,
                    "end_time": 3875.62
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "So if we have uploaded if in Q it should answer yeah so that's the expectation.",
                    "start_time": 3875.7,
                    "end_time": 3879.9
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Let's say we add that okay should answer so we need that flow okay",
                    "start_time": 3879.9,
                    "end_time": 3885.86
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "we'll integrate that for you we'll indicate some basic effort so it'll be an",
                    "start_time": 3886.18,
                    "end_time": 3891.66
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "extra current of the flow plus what Harsh mentioned would be the values.",
                    "start_time": 3891.66,
                    "end_time": 3896.86
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Right.",
                    "start_time": 3896.86,
                    "end_time": 3897.1
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So if you.",
                    "start_time": 3897.1,
                    "end_time": 3897.58
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "If a user wants to ask what was my revenue in January 2023 they should able to answer that as well.",
                    "start_time": 3897.58,
                    "end_time": 3903.29
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 3903.29,
                    "end_time": 3903.57
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "The types of questions would be FPA FAQ related questions or questions about their historical performance.",
                    "start_time": 3903.57,
                    "end_time": 3910.65
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 3910.81,
                    "end_time": 3911.13
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Or also questions about the module two and module three that you've created.",
                    "start_time": 3911.13,
                    "end_time": 3915.29
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 3915.29,
                    "end_time": 3915.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So it might ask you what was my what did I Forecast for revenue May 2026.",
                    "start_time": 3915.53,
                    "end_time": 3922.17
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Right.",
                    "start_time": 3922.17,
                    "end_time": 3922.53
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "So this rag based approach should answer all these types of questions.",
                    "start_time": 3922.53,
                    "end_time": 3926.41
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We have all that included, right?",
                    "start_time": 3927.44,
                    "end_time": 3928.88
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "That's right.",
                    "start_time": 3929.04,
                    "end_time": 3929.68
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We will.",
                    "start_time": 3930.16,
                    "end_time": 3930.8
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We have.",
                    "start_time": 3930.88,
                    "end_time": 3931.36
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "We have done that.",
                    "start_time": 3931.36,
                    "end_time": 3932.52
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Some part of that also.",
                    "start_time": 3932.52,
                    "end_time": 3933.6
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "But yep, it will be covered.",
                    "start_time": 3933.92,
                    "end_time": 3935.44
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yep.",
                    "start_time": 3935.44,
                    "end_time": 3936
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yes.",
                    "start_time": 3936,
                    "end_time": 3936.48
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 3937.2,
                    "end_time": 3937.76
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Just.",
                    "start_time": 3938.96,
                    "end_time": 3939.36
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Just the basic Q and A just which you have mentioned.",
                    "start_time": 3939.44,
                    "end_time": 3942.12
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Right now we just need to include that part only.",
                    "start_time": 3942.12,
                    "end_time": 3944.64
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Other than that like all of the things for the past data which we have, anything forecasted which we have it will be answered by the anything you asked questions related to that.",
                    "start_time": 3945.04,
                    "end_time": 3956.17
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "So Karen, just to.",
                    "start_time": 3957.85,
                    "end_time": 3958.97
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Just to clarify a bit further question that that would be possible for both approaches, is that right?",
                    "start_time": 3958.97,
                    "end_time": 3967.85
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Actually that approach one and two is just for the stress test case.",
                    "start_time": 3968.81,
                    "end_time": 3972.49
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It's nothing to do with the simple Chatbot A.",
                    "start_time": 3972.49,
                    "end_time": 3976.09
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Yeah.",
                    "start_time": 3979.14,
                    "end_time": 3979.5
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yep.",
                    "start_time": 3979.5,
                    "end_time": 3979.86
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It will be done in both if you simple.",
                    "start_time": 3979.86,
                    "end_time": 3982.7
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "If you want a simple answer, it will be done in both.",
                    "start_time": 3982.7,
                    "end_time": 3984.66
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Yeah.",
                    "start_time": 3984.66,
                    "end_time": 3985.06
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 3985.06,
                    "end_time": 3985.54
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "I think the approach one or two is just for the preset question.",
                    "start_time": 3988.34,
                    "end_time": 3991.02
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "That's right.",
                    "start_time": 3991.02,
                    "end_time": 3991.5
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "That's right.",
                    "start_time": 3991.5,
                    "end_time": 3991.94
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "That's right.",
                    "start_time": 3991.94,
                    "end_time": 3992.5
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "We we will be giving.",
                    "start_time": 3993.46,
                    "end_time": 3994.74
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "You'll be using a ragbage approach because you're asking questions and giving all the information whether it's finance terms, FAQs, historical data calculations or you know, forecasted calculations that the model has all that.",
                    "start_time": 3994.74,
                    "end_time": 4010.3
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "And like the previous question when Harsh was showcasing you like how the, like you were saying like it was showing the double the value or the half the value of the.",
                    "start_time": 4013.34,
                    "end_time": 4023.18
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "But what was the cash flow like asking the question like how is the cash flow value showing like showcasing like this.",
                    "start_time": 4023.18,
                    "end_time": 4029.74
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So do you want us to like create a document especially like highlighting like what are the values we get from firstly from the DB and what are the possibilities?",
                    "start_time": 4030.23,
                    "end_time": 4039.27
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "It is gathering, the AI is gathering and then after that like how it is picking one of the possibilities.",
                    "start_time": 4039.35,
                    "end_time": 4044.39
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Do you want any, any of that?",
                    "start_time": 4044.55,
                    "end_time": 4046.47
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yes, that would be.",
                    "start_time": 4046.47,
                    "end_time": 4047.31
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "That would be helpful to see what it's.",
                    "start_time": 4047.31,
                    "end_time": 4049.11
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 4049.11,
                    "end_time": 4049.59
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah.",
                    "start_time": 4049.83,
                    "end_time": 4050.31
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "Then we'll share it by today or most of the tomorrow and you can.",
                    "start_time": 4050.79,
                    "end_time": 4056.32
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "You can go go through that and you can let us know if you.",
                    "start_time": 4056.32,
                    "end_time": 4058.76
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "If you have any concerns over over our approach.",
                    "start_time": 4058.76,
                    "end_time": 4060.96
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "And we also highlight what are the formulas which you use to get the different values.",
                    "start_time": 4061.04,
                    "end_time": 4065.88
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So do you can have a more clarity over like and, and like the possibilities which I'm talking about?",
                    "start_time": 4065.88,
                    "end_time": 4071.24
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "There are a lot of possibilities like, which the AI considers but we'll highlight like five to 10 possibilities like, like, but how it is getting that possibilities will highlight some of the like main things to you.",
                    "start_time": 4071.24,
                    "end_time": 4083.53
                },
                {
                    "speaker_name": "Karan Middha U0438EU2CSX",
                    "text": "So do you can get an idea about that and you can let us know if you have anything about any, any concerns?",
                    "start_time": 4083.53,
                    "end_time": 4088.41
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah.",
                    "start_time": 4092.41,
                    "end_time": 4092.97
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Thank you.",
                    "start_time": 4093.93,
                    "end_time": 4094.49
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Yeah.",
                    "start_time": 4095.37,
                    "end_time": 4095.93
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Okay.",
                    "start_time": 4101.21,
                    "end_time": 4101.89
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Anything else from anyone on the call before we close?",
                    "start_time": 4101.89,
                    "end_time": 4106.49
                },
                {
                    "speaker_name": "Bhavneet Mhajan",
                    "text": "Yeah.",
                    "start_time": 4107.59,
                    "end_time": 4107.83
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Or nothing from a site.",
                    "start_time": 4107.83,
                    "end_time": 4109.19
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Please feel free to message me anytime on WhatsApp if there is any immediate support required.",
                    "start_time": 4111.35,
                    "end_time": 4116.95
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Okay, sure, sure.",
                    "start_time": 4117.03,
                    "end_time": 4118.95
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We will continue.",
                    "start_time": 4119.27,
                    "end_time": 4120.07
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Perfect.",
                    "start_time": 4124.63,
                    "end_time": 4125.11
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Thank you.",
                    "start_time": 4125.67,
                    "end_time": 4126.39
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "So if there's nothing else from anyone then I guess we can close the call.",
                    "start_time": 4126.55,
                    "end_time": 4130.23
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "We've got some actions get you back some information to review.",
                    "start_time": 4130.23,
                    "end_time": 4135.169
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Hopefully the next couple of days will confirm how long that will take after the call and yeah, we can, we can pick it up from then.",
                    "start_time": 4135.249,
                    "end_time": 4144.049
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Sure.",
                    "start_time": 4145.649,
                    "end_time": 4146.049
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "We will provide you with the requested documents and plus whatever we have suggested and then you can finalize according to that.",
                    "start_time": 4146.529,
                    "end_time": 4153.169
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Yeah.",
                    "start_time": 4156.449,
                    "end_time": 4156.849
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "Thank you, Samra.",
                    "start_time": 4156.849,
                    "end_time": 4157.809
                },
                {
                    "speaker_name": "Nolocode AI",
                    "text": "All right, if there's nothing else, then we can close the call for now.",
                    "start_time": 4158.289,
                    "end_time": 4161.409
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Yeah.",
                    "start_time": 4162.11,
                    "end_time": 4162.35
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Thank you so much.",
                    "start_time": 4162.35,
                    "end_time": 4163.15
                },
                {
                    "speaker_name": "Project Manager SFS",
                    "text": "Thank you for time everyone.",
                    "start_time": 4163.15,
                    "end_time": 4164.35
                },
                {
                    "speaker_name": "Harsh Vardhan Dixit",
                    "text": "Thank you, Tim.",
                    "start_time": 4164.99,
                    "end_time": 4165.75
                },
                {
                    "speaker_name": "Ashpreet Singh",
                    "text": "Thank you.",
                    "start_time": 4165.75,
                    "end_time": 4166.27
                }
            ],
              "summary": "null"
            }
        ]
    }
}



