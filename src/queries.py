from datetime import date
from util import ImportantDates

# Base EFTS bitcoin query
base_bitcoin_8k_company_query = {
    "q": "(bitcoin)",
    "dateRange": "custom",
    "startdt": "2020-08-01",
    "enddt": date.today(),
}

# Base EFTS Bitcoin miner query
base_bitcoin_8k_mining_company_query = {
    "q": "(bitcoin OR Bitcoin) AND (FORM 8-K) AND NOT Trust AND mining ",
    "dateRange": "custom",
    "startdt": "2024-12-15",
    "enddt": date.today(),
}
# Base EFTS Bitcoin balance sheet query
base_bitcoin_balance_sheet_query = {
    "q": "(bitcoin OR Bitcoin) AND (purchase OR purchased OR acquire OR acquired OR added OR add)",
    "dateRange": "custom",
    "startdt": "2024-12-30",
    "enddt": date.today(),
}

main_bitcoin_entity_query = {
    "q": 'bitcoin',
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"), 
    "category": "custom",
}

q_1 = {
    "q": 'purchased NEAR(5) bitcoin -"bitcoin mining"',
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2025-01-12",
    "enddt": "2025-02-11",
    "category": "custom",
}

q_2 = {
    "q": 'purchase NEAR(5) bitcoin -"bitcoin mining"',
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2025-01-12",
    "enddt": "2025-02-11",
    "category": "custom",
}

q_3 = {
    "q": 'acquire NEAR(5) bitcoin -"bitcoin mining"',
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2025-01-12",
    "enddt": "2025-02-11",
    "category": "custom",
}

q_4 = {
    "q": 'acquired NEAR(5) bitcoin -"bitcoin mining"',
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2025-01-12",
    "enddt": "2025-02-11",
    "category": "custom",
}
