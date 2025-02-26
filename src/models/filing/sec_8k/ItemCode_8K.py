from enum import Enum
from typing import List, Optional


class ItemCode_8K(Enum):
    # Section 1: Registrant’s Business and Operations
    ITEM_1_01 = "Item 1.01 Entry into a Material Definitive Agreement"
    ITEM_1_02 = "Item 1.02 Termination of a Material Definitive Agreement"
    ITEM_1_03 = "Item 1.03 Bankruptcy or Receivership"
    ITEM_1_04 = (
        "Item 1.04 Mine Safety—Reporting of Shutdowns and Patterns of Violations"
    )
    ITEM_1_05 = "Item 1.05 Material Changes in Business Strategy"  # Added

    # Section 2: Financial Information
    ITEM_2_01 = "Item 2.01 Completion of Acquisition or Disposition of Assets"
    ITEM_2_02 = "Item 2.02 Results of Operations and Financial Condition"
    ITEM_2_03 = "Item 2.03 Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement of a Registrant"
    ITEM_2_04 = "Item 2.04 Triggering Events That Accelerate or Increase a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement"
    ITEM_2_05 = "Item 2.05 Costs Associated with Exit or Disposal Activities"
    ITEM_2_06 = "Item 2.06 Material Impairments"
    ITEM_2_07 = "Item 2.07 Submission of Matters to a Vote of Security Holders"  # Added
    ITEM_2_08 = "Item 2.08 Failure to Satisfy a Listing Rule or Standard"  # Added

    # Section 3: Securities and Trading Markets
    ITEM_3_01 = "Item 3.01 Notice of Delisting or Failure to Satisfy a Continued Listing Rule or Standard; Transfer of Listing"
    ITEM_3_02 = "Item 3.02 Unregistered Sales of Equity Securities"
    ITEM_3_03 = "Item 3.03 Material Modification to Rights of Security Holders"

    # Section 4: Matters Related to Accountants and Financial Statements
    ITEM_4_01 = "Item 4.01 Changes in Registrant’s Certifying Accountant"
    ITEM_4_02 = "Item 4.02 Non-Reliance on Previously Issued Financial Statements or a Related Audit Report or Completed Interim Review"

    # Section 5: Corporate Governance and Management
    ITEM_5_01 = "Item 5.01 Changes in Control of Registrant"
    ITEM_5_02 = "Item 5.02 Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers"
    ITEM_5_03 = "Item 5.03 Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year"
    ITEM_5_04 = "Item 5.04 Temporary Suspension of Trading under Registrant’s Employee Benefit Plans"
    ITEM_5_05 = "Item 5.05 Amendments to the Registrant’s Code of Ethics, or Waiver of a Provision of the Code of Ethics"
    ITEM_5_06 = "Item 5.06 Change in Shell Company Status"  # Added
    ITEM_5_07 = "Item 5.07 Submission of Matters to a Vote of Security Holders"  # Added
    ITEM_5_08 = "Item 5.08 Shareholder Director Nominations"  # Added

    # Section 6: Asset-Backed Securities
    ITEM_6_01 = "Item 6.01 ABS Informational and Computational Material"
    ITEM_6_02 = "Item 6.02 Change of Servicer or Trustee"
    ITEM_6_03 = "Item 6.03 Change in Credit Enhancement or Other External Support"
    ITEM_6_04 = "Item 6.04 Failure to Make a Required Distribution"
    ITEM_6_05 = "Item 6.05 Securities Act Updating Disclosure"

    # Section 7: Regulation FD
    ITEM_7_01 = "Item 7.01 Regulation FD Disclosure"

    # Section 8: Other Events
    ITEM_8_01 = "Item 8.01 Other Events"

    # Section 9: Financial Statements and Exhibits
    ITEM_9_01 = "Item 9.01 Financial Statements and Exhibits"

    # Section 10: Additional General Information (if applicable)
    ITEM_10_01 = "Item 10.01 General Information"  # Added

    @staticmethod
    def from_string(item_code_str: str) -> Optional["ItemCode_8K"]:
        item_code_enum = f"ITEM_{item_code_str.replace('.', '_')}"
        return ItemCode_8K.__members__.get(item_code_enum, None)

    @staticmethod
    def map_item_codes(item_code_strs: List[str]) -> List[Optional["ItemCode_8K"]]:
        return [ItemCode_8K.from_string(code) for code in item_code_strs]

