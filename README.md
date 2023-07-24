# AutomatedTradingAlgoProject
Saurabh Mandlik Personal Automated Algorithmic Trading System.
- LinkedIn : https://www.linkedin.com/in/saurabh-mandlik-ba2bb512a/
- Contact Info: mandliks1996@gmail.com

Description:

- This is currently deployed on my personal EC2 instance [ Red Hat Enterprise Linux ]
- This is an Automated Algorithmic Project which searches for signal as per strategy and will place order.
- This is a Bank Nifty Intraday Trend(Directional) following strategy.
- The setup relies on 3 indicators: Williams Alligator, SupterTrend & PivotPoints.
- The setup is integrated with Telegram, it will send Notification to the user based:
    Whether signal was Found or Not
    If Found: which Option Strike Price order it placed.
    Once placed, if Order is Completed with a certain persiod, the script will start sending Trailing Info.
    If anything is there to Trail it will send Trailing Info
    If an exit was found, it will notify the same
    It also notifies on any Failures.
- I will not disclose Strategy, you can read it and understand for yourself :)

Disclaimer: Except for alligator.py rest code is developed by me. 
