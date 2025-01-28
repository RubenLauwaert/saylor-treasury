from datetime import date

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
