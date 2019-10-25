import requests
import time



# User supplied data

# API key for backpack.tf
# You can obtain one from "https://backpack.tf/developer"
APIKEY = ""

# The average price you obtain Mann Co. Keys for
KEYPRICE = 2.02

# Your key price divided by its metal value
REFPRICE = 0.054299

# Your input files
STEAMINPUT = "steamNames.txt"
CLASSIFIEDINPUT = "classifiedNames.txt"



# Read names from file

def readFile(fileName):
	file = open(fileName,"r")
	names = file.readlines()
	file.close()
	return names



""" 
File validation 
The 2 input file should contain the same number of rows 
"""

def getLength(list1, list2):
	if (len(list1) == len(list2)):
		return len(list1)
	else:
		return 0



# Sort the list by potential profit decreasing

def orderList():
	priceList.sort(key=lambda tup: tup["profit"], reverse=True)



""" 
Write data into 2 files 
Prices file contains the profit, prices, auto-trade status and name
Links contain backpack-steam links to given item
"""

def writeFile(startIndex, endIndex):

	prices = open("prices" + str(startIndex) + "_" + str(endIndex) + ".txt","w")
	links = open("links" + str(startIndex) +"_" + str(endIndex) + ".txt","w") 
 
	for item in priceList:
		prices.write("%.2f \t %.2f \t %.2f \t %d \t %s \t %s \n" % (item["profit"], item["steamPrice"], item["classifiedPrice"], item["automatic"],
		                                                            item["tradePrice"], item["name"]))
		links.write("https://backpack.tf/stats/Unique/" + item["name"] + "/Tradable/Craftable\n")
		links.write("https://steamcommunity.com/market/listings/440/" + item["name"] + "\n")
 
	prices.close()
	links.close()



# Fetches the price data for the "i"th item
def getItem(i):
	
	print(i)
	name = steamNames[i].replace("\n", "")

	# Classified market query 
	classifiedURL = "https://backpack.tf/api/classifieds/search/v1?item_names=1&quality=6&key=" + APIKEY + "&intent=sell&page_size=1&item=" + (classifiedNames[i])
	classifiedResponse = requests.get(classifiedURL)
	classifiedData = classifiedResponse.json()	

	# Steam market query
	steamURL = "https://steamcommunity.com/market/priceoverview/?appid=440&currency=3&market_hash_name=" + (steamNames[i]).replace(' ', '%20')
	steamResponse = requests.get(steamURL)
	steamData = steamResponse.json()

	if (classifiedResponse.status_code == 200 and steamResponse.status_code == 200):

		# Get Steam price

		try:
			steamPrice = steamData["median_price"]
		except Exception as e:
			try:
				steamPrice = steamData["lowest_price"]
			except Exception as e:
				steamPrice = "0€"

		# Strip the currency of the end 4,20€ -> 4,20
		steamPrice = steamPrice[0: len(steamPrice)-1]
		# Replace recimal mark 4,20 -> 4.20
		steamPrice = steamPrice.replace(',', '.')
		# Steam uses 4,-- for even prices, so we replace the '-' with 0s
		steamPrice = steamPrice.replace('-', '0')
		# Steam takes a 12% cut, so our final price is 88% of the original
		steamPrice = (float(steamPrice)) * 0.88



		# Get Classified price

		# Default values	
		classifiedPrice = 100.0
		tradePrice = ""
		automatic = 0

		# Check the number of listings	
		if (classifiedData["sell"]["total"] == 0):
			tradePrice = "No listing"

		# If the name matches the name of the listed item
		elif (name in (classifiedData["sell"]["listings"][0]["item"]["name"])):
			classifiedPrice = classifiedData["sell"]["listings"][0]["currencies"]

			# If the price is given in key + metal
			try:
				keys            = float(classifiedPrice["keys"])
				metal           = float(classifiedPrice["metal"])
				tradePrice	    = "%.2f keys, %.2f ref" % (keys, metal) 
				classifiedPrice = keys * KEYPRICE + metal * REFPRICE
			except Exception as e:

			# If price is given in keys
				try:
					classifiedPrice = float(classifiedPrice["keys"])
					tradePrice      = "%.2f" % (classifiedPrice) + " keys"
					classifiedPrice	= classifiedPrice * KEYPRICE
				except Exception as e:

			# If the price is given in metal
					try:
						classifiedPrice = float(classifiedPrice["metal"])
						tradePrice      = "%.2f" % (classifiedPrice	) + " ref"
						classifiedPrice	= classifiedPrice * REFPRICE

			# Otherwise
					except Exception as e:
						tradePrice = "Error"

			# Check if trade is automatic
			try:
				automatic = classifiedData["sell"]["listings"][0]["automatic"]
			except Exception as e:
				automatic = 0

		# Case where the names do not match
		else:
			tradePrice = "Wrong item"

		tpl = {"name": name, "steamPrice": float(steamPrice), "classifiedPrice": classifiedPrice,
		       "profit": float(steamPrice) - classifiedPrice, "tradePrice": tradePrice, "automatic": automatic, "valid": True}
		return tpl	

	# In case we do not receive code 200 from both queries
	# mark the item as invalid, so the main function retries
	else:
		return({"name": "-", "steamPrice": 0, "classifiedPrice": 0, "profit": 0, "tradePrice": "-", "automatic": 0, "valid": False })	






# Pre-execution setup
priceList = [] # {name, steamPrice, classifiedPrice, profit, tradePrice, automatic, valid}
readyToExecute = True
numOfRows = 0

try:
	steamNames      = readFile(STEAMINPUT)
	classifiedNames = readFile(CLASSIFIEDINPUT)
	numOfRows = getLength(steamNames, classifiedNames)
except IOError:
	print("Cannot read input files")
	readyToExecute = False
if numOfRows == 0:
	print("Problem with the input files")
	readyToExecute = False
if APIKEY == "":
	print("No API key supplied")
	readyToExecute = False
if KEYPRICE == "":
	print("Mann Co. Key price not set")
	readyToExecute = False
if REFPRICE == "":
	print("Refined Metal price not set")
	readyToExecute = False


# Main 
if readyToExecute:

	print("Which items would you like to scan:")
	print("Press '1' for all items")
	print("Press '2' for the first half")
	print("Press '3' for the second half")
	
	choice = input()
	if (choice == "1"):
		startIndex = 0
		endIndex = numOfRows
	elif (choice == "2"):
		startIndex = 0
		endIndex = 99
	elif (choice == "3"):
		startIndex = 100
		endIndex = numOfRows
	else:
		startIndex = 0
		endIndex = numOfRows

	""" 
	Build the priceList
	3 consecutive failed query usually means that the daily query limit is reached, 
	so the program stops executing 
	"""
	for i in range (startIndex, endIndex):
		item = getItem(i)
		if (item["valid"]):
			priceList.append(item)
		else:
			print("Waiting...")
			time.sleep(60)
			item = getItem(i)
			if (item["valid"]):
				priceList.append(item)
			else:
				print("Waiting...")
				time.sleep(60)
				item = getItem(i)
				if (item["valid"]):
					priceList.append(item)
				else:
					break
	orderList()
	writeFile(startIndex, endIndex)
	print("Done")