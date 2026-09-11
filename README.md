# Expense Claims Management System

A lightweight expense claims management system built as part of the VSP Techverse interview assessment.

The application allows staff members to submit expense claims from receipt text, managers to review team claims, and finance users to monitor spending and complete approved payments.

## Features

- Staff can create expense claims by pasting receipt text.
- Receipt text is automatically converted into structured claim details.
- Users can review and edit extracted details before submission.
- Staff can track their monthly spending and remaining limit.
- Managers can review and approve/reject team claims.
- Managers cannot approve their own claims.
- Duplicate receipts are detected to help prevent double payment.
- Finance users can view:
  - Category-wise spending
  - Employee-wise monthly spending
  - Monthly spending limits
  - Near-limit employees
  - Claim payment status
- Approved claims can be marked as paid.
- Paid claims are treated as completed and cannot move backwards.

## Technology Stack

- Python
- Flask
- SQLite
- HTML
- CSS
- Jinja2
- Regular Expressions
- Python difflib for duplicate receipt similarity detection

## Demo Users

| Role | Email | Password |
|---|---|---|
| Staff | staff@demo.com | 1234 |
| Manager | manager@demo.com | 1234 |
| Finance | finance@demo.com | 1234 |
| Staff | arjun@demo.com | 1234 |

## How to Run

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd expense-claims