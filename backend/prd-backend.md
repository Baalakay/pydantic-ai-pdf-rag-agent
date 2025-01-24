# Non-Blank Subcategory Issue PRD

## Problem Statement
The "Test Coil" category in the specifications table is showing "Test Coil" in both the Category and Specification columns, when the Specification column should be blank.

## Current Data Flow
1. PDFProcessor correctly stores subcategories with empty string keys when PDFColumn2 is blank
2. CompareProcessor's `_get_ordered_specs` method correctly maintains this structure
3. Issue appears to be in the `SpecRow` validator not being triggered properly

## Requirements
1. DO NOT modify `process_compare.py` or `process_pdf.py` - this is non-negotiable
2. DO NOT attempt to fix this in `_parse_table_to_specs` - it is working correctly by storing empty subcategory keys
3. The fix MUST be in the `SpecRow` validator to handle cases where specification matches category
4. The validator MUST ensure specifications match the PDF's original structure where certain categories (like "Test Coil") always have blank subcategories

## Attempted Solutions

### Attempt 1: Modify from_models Logic
- Changed `from_models` to let `SpecRow` validator handle empty/matching specifications
- Removed redundant specification check in `from_models`
- Result: Still showing "Test Coil" in both columns
- Issue: Validator might not be getting called

### Attempt 2: Debug SpecRow Initialization
- Added debug output to `SpecRow.__init__` to track initialization flow
- Added debug output to specification setter
- Added print statements to track when specification is being set
- Result: Debug output shows initialization but setter not being called
- Issue: Property setter might be bypassed during initialization

### Attempt 3: Improve SpecRow Initialization
- Modified `__init__` to explicitly call specification setter after super().__init__
- Added more debug output to track specification value at each step
- Result: Still investigating if setter is being called properly
- Issue: Need to verify if frozen=True in ConfigDict is affecting property setter

### Attempt 4: Remove frozen=True from ConfigDict
- Removed frozen=True from SpecRow model_config to allow property setter to work
- Added extensive debug output to track specification value at each step
- Result: Property setter still not being called consistently
- Issue: May be related to latest Pydantic version

### Attempt 5: Switch to Model Validator
- Replaced property setter with @model_validator(mode="before")
- Added debug output to track validation process
- Result: Validator not being called, debug output not showing
- Issue: Validation approach not working as expected

## Current Status
- Confirmed `comparison.py` is being executed (via debug output)
- Multiple approaches to validation have failed
- Debug output suggests validators and property setters are not being called
- Latest Pydantic version (released today) may be causing issues

## Next Steps
1. Downgrade to Pydantic v2.10.5 which is known to work with property setters
2. If downgrade works, document the issue for future reference
3. If downgrade doesn't work, consider alternative validation approaches 