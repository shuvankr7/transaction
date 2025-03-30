import re
import json
import spacy
import streamlit as st
from datetime import datetime
import nltk
from nltk.corpus import stopwords

# Download NLTK stopwords if not already downloaded
nltk.download('stopwords')

# Load NLTK stopwords
nltk_stopwords = set(stopwords.words('english'))
st.set_page_config(
    page_title="Transaction Analyzer",
    page_icon="💳",
)

try:
    import requests
except ImportError:
    st.error("The 'requests' package is not installed. Please add it to your requirements.txt file.")
    # Define a mock requests object to prevent errors
    class MockRequests:
        def get(self, url):
            return None
    requests = MockRequests()

spacy_model = "en_core_web_sm"
try:
    nlp = spacy.load(spacy_model)
except Exception as e:
    st.error(f"Failed to load spaCy model: {str(e)}")
    # Continue without NLP functionality

# Create a hardcoded fallback for the merchant dataset
tag = {}  # Empty dictionary as fallback

# Try to fetch the dataset only if requests is available
if requests.__class__.__name__ != "MockRequests":
    try:
        url = "https://raw.githubusercontent.com/shuvankr7/transaction/main/final_merchant_dataset.json"
        response = requests.get(url)
        
        if response and hasattr(response, 'status_code') and response.status_code == 200:
            tag = response.json()
        else:
            st.error(f"Failed to load merchant dataset. Status code: {getattr(response, 'status_code', 'unknown')}")
    except Exception as e:
        st.error(f"Error loading merchant dataset: {str(e)}")
else:
    st.error("Using a local fallback dataset since 'requests' is not available.")

category_keywords = {
    "Food & Dining": ["restaurant", "food", "dinner", "lunch", "pizza", "cafe", "bar", "mcdonald","zomato","swiggy"],
    "Utilities": ["electricity bill", "water bill", "gas bill", "recharge", "broadband", "internet", "phone bill"],
    "Shopping": ["mall", "shopping", "amazon", "flipkart", "store", "clothing", "apparel"],
    "Transport": ["uber", "ola", "bus", "train", "flight", "petrol", "fuel", "cab"],
    "Entertainment": ["movie", "netflix", "spotify", "concert", "game", "theatre", "amusement park", "cinema"],
    "Healthcare": ["hospital", "clinic", "medicine", "doctor", "pharmacy", "health checkup"],
    "Other": []
}
category_keywords = {
    "Food & Dining": [
        "restaurant", "food", "dinner", "lunch", "pizza", "cafe", "bar", 
        "mcdonald", "zomato", "swiggy", "dominos", "burger king", "subway",
        "kfc", "starbucks", "coffee", "snacks", "biryani", "beverage", "tea",
        "breakfast", "brunch", "dineout"
    ],
    
    "Utilities": [
        "electricity bill", "water bill", "gas bill", "recharge", "broadband", 
        "internet", "phone bill", "dth", "postpaid", "prepaid", "wifi", "cable tv",
        "mobile recharge", "landline", "municipal tax", "sewage", "property tax"
    ],
    
    "Shopping": [
        "mall", "shopping", "amazon", "flipkart", "store", "clothing", "apparel", 
        "footwear", "accessories", "electronics", "gadgets", "laptop", "mobile", 
        "fashion", "jewelry", "eyewear", "furniture", "homedecor", "big bazaar", "reliance trends",
        "meesho", "tatacliq", "nike", "adidas", "puma"
    ],
    
    "Transport": [
        "uber", "ola", "bus", "train", "flight", "petrol", "fuel", "cab", "metro",
        "auto", "rickshaw", "taxi", "diesel", "airfare", "air ticket", "commute",
        "travel", "bike rental", "car rental", "highway toll", "parking"
    ],
    
    "Entertainment": [
        "movie", "netflix", "spotify", "concert", "game", "theatre", "amusement park",
        "cinema", "hotstar", "prime video", "zee5", "bookmyshow", "gaming", "arcade",
        "pubg", "playstation", "xbox", "cricket", "football", "music festival"
    ],
    
    "Healthcare": [
        "hospital", "clinic", "medicine", "doctor", "pharmacy", "health checkup", 
        "dental", "eye test", "surgery", "diagnostic", "pathology", "medical store",
        "covid test", "therapy", "vaccination", "fitness", "gym", "insurance premium"
    ],
    

    
    
    "Other": []
}
TRANSACTION_KEYWORDS = [
    r"\bspent\b", r"\bdebited\b", r"\bcredited\b", r"\btransaction\b",
    r"\bpurchase\b", r"Rs\.?\s?\d+", r"\bsent\b", r"\breceived\b",
    r"\bpaid\b", r"\bwithdrawn\b", r"\bdeposited\b", r"\bcharged\b",
    r"\btransferred\b", r"\bbalance\b", r"\bupi\b", r"\bimps\b",
    r"\bneft\b", r"\brefunded\b", r"\bfailed\b",
    r"\bused for Rs\d+", 
    r"\bused for INR\d+",
    r"\bCard X\d+",
    r"\bTxn#\d+",
    r"X\d{4} used",
    r"to block Card",
    r"\bat\d+",
]

# Non-Transactional Keywords
NON_TRANSACTIONAL_KEYWORDS = [
    r"\bloan\b", r"\bapply now\b", r"\binterest rate\b", r"\bcheck emi\b", r"\blast chance\b", 
    r"\blimited time\b", r"\bdiscount\b", r"\bcashback\b", r"\binsurance\b", r"\bpolicy\b", 
    r"\binvestment\b", r"\bfund bal\b", r"\bsecurities bal\b", r"\bbroker\b", r"\boffer\b", 
    r"\breward\b", r"\bvoucher\b", r"\bgift\b", r"\bprize\b", r"\bbonus\b", r"\bcongrats\b", 
    r"\blucky draw\b", r"\bjackpot\b", r"\bwin\b", r"\bcontest\b", r"\bfree\b", r"\bsubscribe\b", 
    r"\bnewsletter\b", r"\bsurvey\b", r"\bfeedback\b", r"\bsurvey link\b", r"\blifestyle\b", 
    r"\bshopping\b", r"\bstore\b", r"\bcoupon\b", r"\bsale\b", r"\bhurry\b", r"\bupgrade\b", 
    r"\bcredit score\b", r"\bloan approval\b", r"\beligibility\b", r"\bapply today\b", 
    r"\bpre-approved\b", r"\bzero cost\b", r"\bzero interest\b", r"\bhot deal\b", 
    r"\bflash sale\b", r"\bfestive offer\b", r"\bnew launch\b", r"\bno cost emi\b", 
    r"\bpremium\b", r"\bmembership\b", r"\breward points\b", r"\bredeem now\b", 
    r"\bpoints balance\b", r"\bcash bonus\b", r"\bservice due\b", r"\bsubscription\b", 
    r"\btrial period\b", r"\brenewal\b", r"\bpolicy due\b", r"\breminder\b", 
    r"\blimited period\b", r"\bpre-book\b", r"\bearly access\b", r"\bexclusive\b", 
    r"\bvalid till\b", r"\btime-limited\b", r"\bterms apply\b", r"\bconditions apply\b",
    r"\bautopay\b", r"\bsufficient\b"  # Added new keywords here
]

BANK_NAMES = [
    "SBI", "State Bank of India",
    "ICICI", "ICICI Bank",
    "HDFC", "HDFC Bank",
    "Axis", "Axis Bank",
    "Kotak", "Kotak Mahindra Bank",
    "BOB", "Bank of Baroda",
    "PNB", "Punjab National Bank",
    "Yes Bank",
    "IDFC", "IDFC First Bank",
    "Union Bank", "Union Bank of India",
    "Canara Bank",
    "Indian Bank",
    "Central Bank", "Central Bank of India",
    "Bank of India",
    "UCO Bank",
    "Bank of Maharashtra",
    "IndusInd", "IndusInd Bank",
    "RBL", "RBL Bank",
    "Federal Bank",
    "South Indian Bank",
    "Karnataka Bank",
    "Dhanlaxmi Bank",
    "Karur Vysya Bank",
    "Tamilnad Mercantile Bank",
    "J&K Bank", "Jammu and Kashmir Bank",
    "IDBI", "IDBI Bank",
    "Citi", "Citi Bank",
    "Standard Chartered", "Standard Chartered Bank",
    "HSBC", "HSBC Bank",
    "DBS", "DBS Bank",
    "Deutsche", "Deutsche Bank",
    "Barclays", "Barclays Bank",
    "BDN","Bandhan Bank"
]
TRANSACTIONAL_SENDERS = [
    # Banks
    "HDFCBK", "ICICIB", "SBIINB", "AXISBK", "CANBNK", "PNBSMS", "BOIIND", "KOTAKB", 
    "INDBNK", "CENTBK", "UNIONB", "YESBNK", "IDBIBNK", "BOBSMS", "CORPBNK", "INDUSB", 
    "DCBBNK", "RBLBNK", "FEDERALB", "KARNATABK", "SOUTHBNK", "TMBLBNK", "UJJIVNBNK",
    "BARODABNK", "SYNDBNK", "PUNBBNK", "MAHBANK", "IOBCORP", "UCOBANK", "SVCBANK",
    
    # Payment Services
    "PAYTMB", "PHONEPE", "GPAY", "GOOGLEPAY", "JioMoney", "Mobikwik", "CRED", "BHIMUPI", 
    "AMAZONPAY", "FREECHARGE", "OLAMONEY", "LAZYPAYIN", "RAZORPAY", "PAYPAL", "STRIPE",
    "MOBKWIK", "UPIBNK", "IPAYMBK", "YESBANK", "WALLETL", "UPICICI", "IMPSBNK",
    
    # Credit/Debit Card
    "VISACARD", "MASTERCRD", "RUPAYCARD", "AMEXCARD", "DCBCARD", "HDFCCARD", "ICICICARD", 
    "SBICARD", "AXISCARD", "BOBCARD", "INDUSCARD", "YESCARD", "AUCARD", "RBLCARD",
    "KOTAKCARD", "PNBCARD", "HSBC", "CITIBANK", "CITICARD", "SCBCARD", "ONECARD", 

]
def is_transactional(message, sender=None):
    """
    Determine if a message is transactional based on sender and content.
    
    Args:
        message (str): The message content
        sender (str): The sender ID/name (optional)
    
    Returns:
        bool: True if transactional, False otherwise
    """
    # If sender is provided, check if it's a known transactional sender
    if sender is not None:
        sender = sender.upper()  # Normalize sender name
        
        # Check if it's a known transactional sender
        if any(trans_sender in sender for trans_sender in TRANSACTIONAL_SENDERS):
            return True
        
        # Check if it's a numeric sender (typically used by banks/businesses)
        if any(char.isdigit() for char in sender) and len(sender) <= 6:
            return True
            
        # Check if it's a sender ID in VM-XXXXXX format (common for Indian bank SMS)
        if re.match(r'^[A-Z]{2}-[A-Z0-9]{6}$', sender):
            return True
        
        # If sender appears to be a personal contact, treat as non-transactional
        if sender.isalpha() and len(sender) > 3:  # Simple heuristic for personal names
            return False
    
    # If no conclusive determination from sender, fall back to content analysis
    message_lower = message.lower()
    
    # Additional contextual checks to identify personal messages
    personal_indicators = [
        r"sent you \d+",         # Matches "sent you 100"
        r"i sent",               # Matches "I sent"
        r"i've sent",            # Matches "I've sent"
        r"sending you",          # Matches "sending you"
        r"let me know",          # Common in personal messages
        r"how are you",          # Common in personal messages
        r"call me",              # Common in personal messages
        r"meet up",              # Common in personal messages
        r"miss you",             # Common in personal messages
        r"love you",             # Common in personal messages
        r"see you",              # Common in personal messages
        r"talk to you",          # Common in personal messages
        r"tell me",              # Common in personal messages
        r"what's up",            # Common in personal messages
        r"how's it going"        # Common in personal messages
    ]
    
    # Check for personal message indicators
    if any(re.search(pattern, message_lower) for pattern in personal_indicators):
        return False
    
    # Check for non-transactional keywords
    if any(re.search(pattern, message_lower) for pattern in NON_TRANSACTIONAL_KEYWORDS):
        return False
        
    # Check for transactional keywords
    return any(re.search(pattern, message_lower) for pattern in TRANSACTION_KEYWORDS)

def extract_transaction_details(message):
    """Extract transaction details from a message if it is transactional."""

    if not is_transactional(message):
        return None  # Ignore non-transactional messages
    entity_pattern = re.compile(r'\b(at|from|to|via|through|with)\s+(.+?)(?=\s+\b(?:at|from|to|via|through|with)|\s*$)', re.IGNORECASE)
    merchant_pattern = re.compile(r'(?i)(?:\sat\s|in\*)([A-Za-z0-9]*\s?-?\s?[A-Za-z0-9]*\s?-?\s?)')
    entities = entity_pattern.findall(message)
    merchants = []
    for preposition, entity in entities:
        if preposition.lower() in ['at', 'to']:
            merchants.append(entity)
    merchant_match = merchant_pattern.search(message)
    merchant = merchant_match.group(1).strip() if merchant_match else (merchants[0].strip() if merchants else None)
    
    # Filter out merchants that are purely numeric
    if merchant and merchant.isdigit():
        merchant = None
    
    # Keep the original merchant name intact
    original_merchant = merchant
    
    # Truncate merchant name at the first stopword or invalid character for tag searching
    truncated_merchant = ""
    if merchant:
        merchant_parts = merchant.split()
        truncated_parts = []
        for part in merchant_parts:
            if part.lower() in nltk_stopwords:  # Use globally defined nltk_stopwords
                break
            truncated_parts.append(part)
        truncated_merchant = ' '.join(truncated_parts).strip()
    


    amount_match = re.search(r"(?i)(?:rs\.?|₹|inr|\$|aed)\s*([\d,]+(?:\.\d{1,2})?)|debited by\s*([\d,]+(?:\.\d{1,2})?)",message,)
    if amount_match:
      amount = amount_match.group(1) or amount_match.group(2)
      amount = float(amount.replace(",", "")) if amount else None
    else:
      amount = None

    # transaction_date = datetime.now().strftime("%d-%m-%y")
     # Extract Transaction Date (Handles different formats)
    date_patterns = [
         r"(\d{2}[-/]\d{2}[-/]\d{2,4})",     # dd/mm/yy, dd/mm/yyyy, dd-mm-yy, dd-mm-yyyy
         r"(\d{2}\.\d{2}\.\d{2,4})",         # dd.mm.yy, dd.mm.yyyy
         r"(\d{2}[A-Za-z]{3}\d{2,4})",       # ddmmmyy, ddmmmyyyy (e.g., 15MAR25)
         r"([A-Za-z]{3}\d{2}\d{2,4})",       # mmmddyy, mmmddyyyy (e.g., MAR1525)
         r"(\d{2}/\d{2}/\d{2,4})",           # mm/dd/yy, mm/dd/yyyy
         r"(\d{2}-\d{2}-\d{2,4})",           # mm-dd-yy, mm-dd-yyyy
         r"(\d{2}\d{2}\d{2})",               # ddmmyy (without separator, e.g., 150325)
         r"(\d{2}\.\d{2}\.\d{4})",           # mm.dd.yyyy
         r"(\d{2}\.\d{2}\.\d{2})",           # mm.dd.yy
         r"(\d{2}[/.-][A-Za-z]{3}[/.-]\d{2,4})",  # dd/mmm/yy, dd/mmm/yyyy, dd-mmm-yy, dd-mmm-yyyy, dd.mmm.yy, dd.mmm.yyyy
     ]
 
    for pattern in date_patterns:
        match = re.search(pattern, message)
        if match:
            date_str = match.group(1)
            break
        else:
            date_str = None
 
     # List of possible date formats to handle different cases
    date_formats = [
         "%d/%m/%y", "%d/%m/%Y", "%d-%m-%y", "%d-%m-%Y",  # dd/mm/yy, dd/mm/yyyy
         "%d.%m.%y", "%d.%m.%Y",  # dd.mm.yy, dd.mm.yyyy
         "%d%b%y", "%d%b%Y",      # ddmmmyy, ddmmmyyyy
         "%b%d%y", "%b%d%Y",      # mmmddyy, mmmddyyyy
         "%m/%d/%y", "%m/%d/%Y",  # mm/dd/yy, mm/dd/yyyy
         "%m-%d-%y", "%m-%d-%Y",  # mm-dd-yy, mm-dd-yyyy
         "%m.%d.%y", "%m.%d.%Y",  # mm.dd.yy, mm.dd.yyyy
         "%d%m%y",                # ddmmyy
         "%d/%b/%y", "%d/%b/%Y",  # dd/mmm/yy, dd/mmm/yyyy
         "%d-%b-%y", "%d-%b-%Y",  # dd-mmm-yy, dd-mmm-yyyy
         "%d.%b.%y", "%d.%b.%Y",  # dd.mmm.yy, dd.mmm.yyyy
     ]
 
     # Try different date formats until successful
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            formatted_date = parsed_date.strftime("%d-%m-%y")  # Convert to dd-mm-yy format
            transaction_date = formatted_date
        except ValueError:
            continue

    # Extract Transaction Type (Credit/Debit)
    transaction_type = None
    message_lower = message.lower()
    if any(word in message_lower for word in ["spent", "debited", "payment", "used at", "charged", "sent","debit"]):
        transaction_type = "Debit"
    elif any(word in message_lower for word in ["credited", "received", "refund", "reversed","credit"]):
        transaction_type = "Credit"

    # Extract Bank Name (Using predefined list)
    bank_name = None
    bank_match = re.search(r"\b(" + "|".join(BANK_NAMES) + r")\b", message, re.IGNORECASE)
    
    if bank_match:
        bank_name = bank_match.group(1).upper()  # Ensure consistent formatting



    # Extract Card Type
    card_type = None
    if re.search(r"Credit Card", message, re.IGNORECASE):
        card_type = "Credit Card"
    elif re.search(r"Debit Card", message, re.IGNORECASE):
        card_type = "Debit Card"
    elif re.search(r"\b(Avl Lmt|Available Limit|Avlbl Lmt|avl limit)\b", message, re.IGNORECASE):
        card_type = "Credit Card"
    elif re.search(r"Avl Bal", message, re.IGNORECASE):  
        card_type = "Debit Card"
    elif re.search(r"Card", message, re.IGNORECASE):  
        card_type = "Card"

    # Extract Merchant Name (Enhanced patterns)
    merchant = None
    t= None
    sender = None
    recipient = None

    # Patterns to extract recipient (where money is going)
    recipient_patterns = [
        r"spent on your .*? at (.*?) on",  # Matches "spent on your SBI Credit Card at Alliance Landline Bill on ..."
        r"spent using .*? on \d{2}-\w{3}-\d{2,4} on (.*?)\s+-",  # Matches "spent using ICICI Bank Card XX2010 on 09-Mar-25 on IND*Amazon.in -"
        r"sent (?:Rs\.?|INR|₹)?\s*\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})? from .*? to ([\w@.-]+)",  # Matches "Sent Rs.100.00 from Kotak Bank AC X4726 to paytm-8727353@ptybl ..."
        r"debited for .*? Transaction Reference Number.*? - ([\w\s]+)",  # Matches "Your Apay Wallet balance is debited for INR 3740.00 - Powered by Juspay"
        r"done at ([\w*.-]+)",  # Matches "transaction done at 42281386"
    ]

    # Patterns to extract sender (where money is coming from)
    sender_patterns = [
        r"received .*? in your .*? from ([\w@.-]+)",  # Matches "Received Rs.3740.00 in your Kotak Bank AC X4726 from amazonpay..."
        r"credited to .*? by ([\w@.-]+)",  # Matches "Rs.5000 credited to your account by HDFC Bank"
        r"refund from ([\w@.-]+)",  # Matches "Refund from Flipkart received"
    ]

    # Extract recipient (where money is going)
    for pattern in recipient_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            recipient = match.group(1).strip()
            break

    # Extract sender (where money is coming from)
    for pattern in sender_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            sender = match.group(1).strip()
            break

    if transaction_type == "Credit":
        merchant = sender
    elif transaction_type == "Debit":
        merchant = recipient

    if merchant != None:
      for k in tag.keys():
        for v in tag[k]:
          if merchant in v:
            tk = k
            break

    # Extract Transaction Mode (Enhanced detection)
    transaction_mode = None
    if card_type !=None:
        transaction_mode = card_type
    elif "upi" in message_lower:
        transaction_mode = "UPI"
    elif "imps" in message_lower:
        transaction_mode = "IMPS"
    elif "neft" in message_lower:
        transaction_mode = "NEFT"
    elif "rtgs" in message_lower:
        transaction_mode = "RTGS"
    elif "netbanking" in message_lower:
        transaction_mode = "NetBanking"
    elif "wallet" in message_lower:
        transaction_mode = "Wallet"
    elif "card" in message_lower:
        transaction_mode = "Card Payment"

    # Extract Reference Number (Improved extraction)
    ref_match = re.search(r"(?:Ref No\.?|UPI Ref|Transaction Reference Number)\s?(\d+)", message, re.IGNORECASE)
    reference_number = ref_match.group(1) if ref_match else None


    category = None
    text_lower = message.lower()
    for c, keywords in category_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            category= c
    tags=[t,category]
    tags.remove(None)
    if transaction_type == None and card_type == "Debit Card":
        transaction_type = "Debit"
    if size(truncated_merchant.split())1:
        truncated_merchant=truncated_merchant.split()[0]+" "+truncated_merchant.split()[1]

    return {
        "Amount": amount,
        "Transaction Type": transaction_type,
        "Bank Name": bank_name,
        "Card Type": card_type,
        "Merchant": truncated_merchant,
        "Transaction Mode": transaction_mode,
        "Transaction Date": transaction_date,
        "Reference Number": reference_number,
        "tag":tags,
        
    }



msg = st.text_input('Enter your messege: ')

if st.button('Predict'):
  t = extract_transaction_details(msg)
  st.write(t)
