from flask import Flask, render_template, request, redirect, session, jsonify #
import os
from time import time
from wallet import Wallet
from wallet import Account
import firebase_admin
from firebase_admin import credentials
#
from datetime import datetime, timedelta
import requests
import plotly.graph_objs as go
import plotly.io as pio

from flask_cors import CORS

STATIC_DIR = os.path.abspath('static')

app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)
app.use_static_for_root = True

myWallet =  Wallet()
account = None
allAccounts = []
user= None
isSignedIn = False
receiverAddress = None
tnxAmount = None
requestUrl = None
paymentStatus = "False"

def firebaseInitialization():
    cred = credentials.Certificate("config/serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://blockchain-wallet-a2812-default-rtdb.firebaseio.com'})
    print("🔥🔥🔥🔥🔥 Firebase Connected! 🔥🔥🔥🔥🔥")

firebaseInitialization()

@app.route("/", methods= ["GET", "POST"])
def home():
    global myWallet, account, allAccounts, isSignedIn, receiverAddress, tnxAmount
    isConnected = myWallet.checkConnection()
   
    balance = "No Balance"
    transactions = None

    if(isSignedIn):
        allAccounts = myWallet.getAccounts()
        if(account == None and allAccounts):
            account = allAccounts[0]

        if(account):
            if(type(account) == dict):
                balance = myWallet.getBalance(account['address'])
                transactions = myWallet.getTransactions(account['address'])
            else:
                balance = myWallet.getBalance(account.address)
                transactions = myWallet.getTransactions(account.address)
        
    ##############
    gas_price = get_gas_price()
    ethereum_price_data = get_eth_price_data()

    if gas_price and ethereum_price_data:
        timestamps, prices = zip(*ethereum_price_data)
        timestamps = [timestamp.strftime('%Y-%m-%d') for timestamp in timestamps]

    ###############

    return render_template('index.html', 
                        isConnected=isConnected,  
                        account= account, 
                        balance = balance, 
                        transactions = transactions, 
                        allAccounts=allAccounts,
                        isSignedIn = isSignedIn,
                        gas_price=gas_price, timestamps=timestamps, prices=prices, ###
                        receiverAddress = receiverAddress,
                        tnxAmount = tnxAmount
                        )



@app.route("/makeTransaction", methods = ["GET", "POST"])
def makeTransaction():
    global myWallet, account, receiverAddress, tnxAmount, requestUrl, paymentStatus

    receiver = request.form.get("receiverAddress")
    amount = request.form.get("amount")

    if(receiverAddress):
        receiver = receiverAddress
        amount = tnxAmount

    privateKey = None
    if(type(account) == dict):
            privateKey = account['privateKey']
            sender= account['address']
    else:
            privateKey = account.privateKey
            sender= account.address

    privateKey = account['privateKey']

    tnxHash = myWallet.makeTransactions(sender, receiver, amount, privateKey)
    myWallet.addTransactionHash(tnxHash, sender, receiver,amount)

    if(receiverAddress):
        receiverAddress = None
        tnxAmount =None
        paymentStatus = True           
    return redirect("/")


@app.route("/createAccount", methods= ["GET", "POST"])
def createAccount(): 
    global account, myWallet
    username = myWallet.username
    account = Account(username)
    return redirect("/")

@app.route("/changeAccount", methods= ["GET", "POST"])
def changeAccount(): 
    global account, allAccounts
    
    newAccountAddress = int(request.args.get("address"))
    account = allAccounts[newAccountAddress]
    return redirect("/")

@app.route("/signIn", methods= ["GET", "POST"])
def signIn(): 
    global account, allAccounts, isSignedIn, myWallet
    isSignedIn = True
    
    username = request.form.get("user")
    password = request.form.get("password")
    
    isSignedIn = myWallet.addUser(username, password)
    return redirect("/")

@app.route("/signOut", methods= ["GET", "POST"])
def signOut(): 
    global account, allAccounts, isSignedIn
    isSignedIn = False
    return redirect("/")

API_KEY = 'EIWQCHMWYYNAC3CIP6NAITGXEG9Y2A1DV7'

def get_gas_price():
    url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if data['status'] == '1':
        gas_data = data['result']
        return {
            'low': int(gas_data['SafeGasPrice']),
            'average': int(gas_data['ProposeGasPrice']),
            'fast': int(gas_data['FastGasPrice'])
        }
    else:
        return None

def get_eth_price_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    params = {
        "vs_currency": "usd",
        "ids": "ethereum",
        "from": int(start_date.timestamp()),
        "to": int(end_date.timestamp()),
        "days": "180",
        "interval": "daily"
    }

    response = requests.get("https://api.coingecko.com/api/v3/coins/ethereum/market_chart", params=params)
    data = response.json()

    if "prices" in data:
        return [(datetime.utcfromtimestamp(entry[0] / 1000), entry[1]) for entry in data["prices"]]
    else:
        return []
    
@app.route('/gas_price_data')
def gas_price_data():
    gas_price = get_gas_price()
    if gas_price:
        return jsonify(gas_price)
    else:
        return jsonify(error="Failed to fetch gas prices.")


#Update the /payment decorator to handle POST requests 
@app.route('/payment', methods=['POST'])
def payment():
    global receiverAddress, tnxAmount, requestUrl, paymentStatus
   # Get JSON data from the request body    

   
   
    if receiverAddress == "voltMillsAdress":
        receiverAddress = "0x2F14facA3dC39d8f0018d767fF5AAf1075D9EA8f"
        print(receiverAddress)
    else:
        print("Didn't receive the address")
    
    # requestUrl = request.base_url

    
    paymentStatus = "processing"
    print("*******", request.url, "********************************************")
    # You can return a JSON response if needed

    # Return the response_data
    return jsonify()

@app.route('/checkPaymentStatus')
def checkPaymentStatus():
    global paymentStatus
    print(paymentStatus)
    return jsonify(paymentStatus)

if __name__ == '__main__':
    app.run(debug = True, port=4000)



