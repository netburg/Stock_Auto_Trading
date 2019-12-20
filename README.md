Warning: Only qualified day-trader could use this script. Please note that using this script may be risky and lead to trading loss. 

High Frequency Trading Condithions：

1 volume/shares outstanding）>2.5% (Not realized yet. To be developed.)
2 buy if a decrease >2% in 20 seconds 
4 sell at purchase price * 101% immediately when buy order completed.
5 pending orders for one stock < 3
6 Forced sale：sell if hold for 3 workdays and a 20% loss (Not realized yet. To be developed.)
7 Data server: local SQL Server (window connection)
8 When get your fist token, please use script in Note No.1 and copy that to file 'access_token.txt'.
9 Each deal is set <$50. It could be customized by yourself.
10 Requests to TDAmeritrade is limited to 120 times in 2 minutes.

The script is being tested and needs to be refined. 
Please do not use it for profit purpose. Copyright reserved.
If you have any questions, please feel free to contact me at zhangjinprc@gmail.com.
