import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


# add firebase config here
firebase_config={
  "type": os.getenv("TYPE"),
  "project_id": os.getenv("PROJECT_ID"),
  "private_key_id": os.getenv("PRIVATE_KEY_ID"),
  "private_key": os.getenv("PRIVATE_KEY"),
  "client_email": os.getenv("CLIENT_EMAIL"),
  "client_id": os.getenv("CLIENT_ID"),
  "auth_uri":  os.getenv("AUTH_URI"),
  "token_uri": os.getenv("TOKEN_URI"),
  "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
  "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
  "universe_domain": os.getenv("UNIVERSE_DOMAIN")
}



cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred)
db=firestore.client()







# Reference to your collection
collection_name = "stocks"


query = db.collection(collection_name)
docs = query.stream()

docs_list = [doc.to_dict() for doc in docs]
print(docs_list)

# first filter of pe
stocks_under_pe_list=[]

for i in docs_list:
    if i["current_pe"] < i["industry_pe"]:
        stocks_under_pe_list.append(i)

print("stocks under pe list"+" "+ str(stocks_under_pe_list))

#second filter
debt_list=[]
for k in stocks_under_pe_list:
    if k["debt_equity_ratio"]<1:
        debt_list.append(k)

print("debt list"+" "+ str(debt_list))


# third filter of highest cp10
cp10_list = []
sorted_debt_list = sorted(debt_list, key=lambda stock: (stock["cp10"], stock["cp5"], stock["cp3"]), reverse=True)

for stock in sorted_debt_list:
    cp10_list.append(stock)
print("cp10 list" +" "+ str(cp10_list))

# third filter of roe
sorted_debt_list = sorted(debt_list, key=lambda x: x['roe'], reverse=True)

roe_list = sorted_debt_list

print("roe list: " + str(roe_list))



#third filter of roce
sorted_debt_list = sorted(debt_list, key=lambda x: x['roce'], reverse=True)

roce_list = sorted_debt_list

print("roce list: " + str(roce_list))




# third filter of consistent growth
consistent_growth_list =[]
def get_consistency(profit_list):
    consistency = 0
    for i in range(1, len(profit_list)):
        if profit_list[i] >= profit_list[i-1]:
            percent_change = ((profit_list[i] - profit_list[i-1]) / profit_list[i-1]) * 100
            consistency += percent_change
    return consistency

consistency_list = []
for obj in debt_list:
    consistency = get_consistency(obj['netProfitList'])
    consistency_list.append((obj, consistency))

sorted_list = sorted(consistency_list, key=lambda x: x[1], reverse=True)
consistent_growth_list = [obj for obj, _ in sorted_list]

print("consistent growth list :- "+str(consistent_growth_list))

new_array = [roce_list, roe_list, consistent_growth_list, cp10_list]
rank = {}

for q in new_array:
    for index, r in enumerate(q):
        # If the stock name is already in rank, add the index to its score
        if r["name"] in rank:
            rank[r["name"]]["score"] += index
        else:
            # Initialize with stock details and its score
            rank[r["name"]] = {"details": r, "score": index}

def get_keys_sorted_by_value(obj):
    # Sort by the score while retaining the details
    return [value["details"] for key, value in sorted(obj.items(), key=lambda item: item[1]["score"])]

final_array = get_keys_sorted_by_value(rank)
print(final_array)
print(rank)




sender_email = os.getenv("EMAIL")
receiver_email = os.getenv("RECEIVER")
password = os.getenv("PASSWORD")
subject = "Stock Recommendation "
body = ""


for ind, final_stock in enumerate(final_array):
    industry_pe_change = round(((final_stock["industry_pe"]-final_stock["current_pe"])/final_stock["current_pe"])*100,2)
    median_pe_change = round(final_stock["medianPe"] - final_stock["current_pe"],2)
    current_price = final_stock["currentPrice"]
    current_roe = final_stock["roe"]
    current_roce  = final_stock["roce"]
    current_cp10 = final_stock["cp10"]
    name = final_stock["name"]
    body = body + f"{ind}.{name} \nchange from industry pe is:- {industry_pe_change}% \nchange from median pe is :- {median_pe_change} \ncurrent roe is :- {current_roe} \ncurrent roce is :- {current_roce} \ncurrent cp10 is:- {current_cp10}\n\n"


print(body)




# Create the email message
msg = MIMEMultipart()
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = subject

# Attach the email body
msg.attach(MIMEText(body, "plain"))

# Connect to the SMTP server and send the email
try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()  # Upgrade the connection to secure
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")







# print(len(docs_list))

# # 1.profit filter
# intrinsic_filter_list = []
# share_list = []
# share_name_list = []
# cp10 = []
#
#
# for i in docs_list:
#     # print("share value")
#     # print(i["mcap"]/i["currentPrice"])
#     intrinsic_filter_list.append(i["free_cash_flow"]["list"])
#     share_list.append(i["mcap"]*10000000/i["currentPrice"])
#     share_name_list.append(i["name"])
#     cp10.append(i["cp10"])
#
#
# print(intrinsic_filter_list)
# print(share_list)
# print(share_name_list)
#
#
# # def analyze_company_growth_and_consistency(profit_data):
# #     """
# #     Analyze company growth and consistency, returning a list of companies ordered by their combined growth and consistency score.
# #     Handles negative and zero profit values by excluding companies with invalid data.
# #
# #     Parameters:
# #         profit_data (dict): A dictionary with company names as keys and lists of profits as values.
# #                             Each list represents profits for a single company over time.
# #
# #     Returns:
# #         list: A list of company names sorted from highest to lowest combined growth and consistency score.
# #     """
# #     company_scores = {}
# #
# #     for company, profits in profit_data.items():
# #         # Check for negative or zero profits
# #         if any(p <= 0 for p in profits):
# #             print(f"Warning: Company {company} has non-positive profits, skipping analysis.")
# #             continue
# #
# #         # Calculate CAGR
# #         n = len(profits)
# #         cagr = (profits[-1] / profits[0]) ** (1 / (n - 1)) - 1
# #
# #         # Calculate consistency as the standard deviation of percentage changes
# #         percentage_changes = np.diff(profits) / profits[:-1]
# #         consistency = np.std(percentage_changes)
# #
# #         # Combine CAGR and consistency into a single score
# #         # Here we simply average the CAGR and consistency, but you could apply weights if desired
# #         combined_score = cagr / (1 + consistency)  # Higher score = better (higher growth and lower inconsistency)
# #
# #         company_scores[company] = combined_score
# #
# #     # Sort companies by the combined score in descending order
# #     sorted_companies = sorted(company_scores.items(), key=lambda x: x[1], reverse=True)
# #
# #     # Return the list of companies ordered by their combined score
# #     return [company for company, _ in sorted_companies]
# #
# # sorted_companies = analyze_company_growth_and_consistency(profit_filter_list)
# # print("Companies sorted by highest to lowest combined growth and consistency:")
# # for company in sorted_companies:
# #     print(company)
#
# def calculate_cagr(values):
#     """
#     Calculate the Compound Annual Growth Rate (CAGR) from a list of numbers.
#
#     Parameters:
#         values (list): A list of numerical values representing growth over time.
#
#     Returns:
#         float: The CAGR value as a decimal.
#     """
#     if len(values) < 2:
#         raise ValueError("The list must contain at least two values to calculate CAGR.")
#
#     starting_value = values[0]
#     ending_value = values[-1]
#     periods = len(values) - 1
#
#     cagr = (ending_value / starting_value) ** (1 / periods) - 1
#     return cagr*100
#
# def calculate_intrinsic_value(fcf, growth_rate, discount_rate, perpetual_growth_rate, num_years, shares_outstanding):
#     print(fcf)
#     print(growth_rate)
#     print(discount_rate)
#     print(perpetual_growth_rate)
#     print(num_years)
#     print(shares_outstanding)
#     """
#     Calculate the intrinsic value of a company using the Discounted Cash Flow (DCF) method.
#
#     Parameters:
#     fcf (float): Current free cash flow (most recent year's FCF).
#     growth_rate (float): Annual growth rate for FCF (in percentage, e.g., 8 for 8%).
#     discount_rate (float): Discount rate (in percentage, e.g., 10 for 10%).
#     perpetual_growth_rate (float): Perpetual growth rate for FCF beyond the forecast period (in percentage, e.g., 4 for 4%).
#     num_years (int): Number of years to project FCF.
#     shares_outstanding (int): Total number of shares outstanding.
#
#     Returns:
#     float: Intrinsic value per share.
#     """
#     # Convert percentages to decimals
#     growth_rate /= 100
#     discount_rate /= 100
#     perpetual_growth_rate /= 100
#
#     # Step 1: Project future FCFs for the forecast period
#     projected_fcfs = []
#     for year in range(num_years):
#         fcf = fcf * (1 + growth_rate)
#         projected_fcfs.append(fcf)
#
#     # Step 2: Calculate Terminal Value
#     terminal_fcf = projected_fcfs[-1] * (1 + perpetual_growth_rate)
#     terminal_value = terminal_fcf / (discount_rate - perpetual_growth_rate)
#
#     # Step 3: Discount FCFs and Terminal Value to present value
#     discounted_fcfs = [fcf / ((1 + discount_rate) ** (year + 1)) for year, fcf in enumerate(projected_fcfs)]
#     discounted_terminal_value = terminal_value / ((1 + discount_rate) ** num_years)
#
#     # Step 4: Calculate Total Present Value
#     total_present_value = sum(discounted_fcfs) + discounted_terminal_value
#
#     # Step 5: Calculate Intrinsic Value Per Share
#     intrinsic_value_per_share = total_present_value / shares_outstanding
#
#     return intrinsic_value_per_share
#
#
# for index,value in enumerate(intrinsic_filter_list):
#     print("value")
#     print(value[-1])
#     print(share_name_list[index])
#     current_cagr=calculate_cagr(value)
#     print("cagr:- "+ str(current_cagr))
#     share_Value = calculate_intrinsic_value(value[-1]*10000000,current_cagr,cp10[index],5,10,share_list[index])
#     print("share value:- " +str(share_Value))
