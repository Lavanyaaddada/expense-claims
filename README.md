# Expense Claims Management System

A lightweight expense claims management system built as part of the VSP Techverse interview assessment.

The application manages the complete expense claim workflow from receipt-based claim submission to manager approval and finance payment.

## Features

- Staff can submit expense claims by pasting receipt text.
- Receipt details are automatically extracted.
- Users can review and edit extracted details before submission.
- Staff can track monthly spending and remaining limits.
- Managers can approve or reject team claims.
- Managers cannot approve their own claims.
- Finance can monitor employee and category-wise spending.
- Monthly spending limits are displayed.
- Duplicate receipts are detected to help prevent double payment.
- Approved claims can be marked as paid.
- Paid claims are treated as completed.

## Technology Stack

- Python
- Flask
- SQLite
- HTML
- CSS
- Jinja2
- Regular Expressions
- Python difflib for duplicate receipt detection

## Demo Users

| Role | Email | Password |
|------|-------|----------|
| Staff | staff@demo.com | 1234 |
| Manager | manager@demo.com | 1234 |
| Finance | finance@demo.com | 1234 |
| Staff | arjun@demo.com | 1234 |

## How to Run

### 1. Clone the repository

git clone https://github.com/Lavanyaaddada/expense-claims.git

cd expense-claims

### 2. Install dependencies

pip install Flask gunicorn

### 3. Run the application

python app.py

Open http://127.0.0.1:5000 in your browser.

## Key Decisions and Assumptions

- SQLite is used as a lightweight database for this assessment.
- Receipt information is entered as text instead of using a paid OCR service.
- Receipt details are extracted using pattern matching and keywords.
- Users can review and correct extracted information before submission.
- Duplicate detection checks receipt details and text similarity.
- Managers cannot approve their own claims.
- Paid claims cannot move back to an earlier stage.
- Finance payment is simulated inside the application.

## Duplicate Receipt Prevention

The system checks new claims against existing claims using merchant name, amount, date and receipt text similarity.

This helps identify duplicate submissions even when the same receipt is entered using slightly different wording.

## AI Tools Used

ChatGPT was used during development for:

- Application structure and Flask implementation assistance
- Debugging and troubleshooting
- Generating realistic sample receipt data
- Documentation and README preparation
- Walkthrough video script preparation

The application functionality was manually tested in the deployed application.

## Deployment

The application is deployed as a live web application using Render.

Live application:

https://expense-claims-sr6s.onrender.com/login

## What I Would Improve With Another Week

- Add actual receipt image upload and OCR.
- Improve duplicate detection with a more advanced matching approach.
- Add email notifications for claim status changes.
- Add automated tests.
- Add stronger authentication and authorization.
- Add more Finance reports and charts.
- Improve mobile responsiveness.
- Use a production-grade database such as PostgreSQL.

## Project Workflow

Staff → Submit Claim → Manager Review → Approve/Reject → Finance → Payment → Completed