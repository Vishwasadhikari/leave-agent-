import boto3

ses = boto3.client(
    "ses",
    region_name="eu-north-1"
)

SENDER_EMAIL = "vishwaslucky98@gmail.com"


def send_approval_email(
    manager_email,
    employee_name,
    leave_type,
    start_date,
    end_date,
    reason,
    request_id,
):
    approve_url = (
        f"https://h5xhhhzgc3s23p2747qatbazm40arsta.lambda-url.eu-north-1.on.aws/"
        f"?action=approve&request_id={request_id}"
    )

    reject_url = (
        f"https://h5xhhhzgc3s23p2747qatbazm40arsta.lambda-url.eu-north-1.on.aws/"
        f"?action=reject&request_id={request_id}"
    )

    html = f"""
    <html>
    <body>

    <h2>Leave Approval Request</h2>

    <p><b>Employee:</b> {employee_name}</p>

    <p><b>Leave Type:</b> {leave_type}</p>

    <p><b>From:</b> {start_date}</p>

    <p><b>To:</b> {end_date}</p>

    <p><b>Reason:</b></p>

    <p>{reason}</p>

    <br>

    <a href="{approve_url}"
       style="padding:12px 25px;
       background:green;
       color:white;
       text-decoration:none;
       border-radius:6px;">
       Approve
    </a>

    &nbsp;&nbsp;

    <a href="{reject_url}"
       style="padding:12px 25px;
       background:red;
       color:white;
       text-decoration:none;
       border-radius:6px;">
       Reject
    </a>

    </body>
    </html>
    """

    ses.send_email(
        Source=SENDER_EMAIL,
        Destination={
            "ToAddresses": [manager_email]
        },
        Message={
            "Subject": {
                "Data": "Leave Approval Required"
            },
            "Body": {
                "Html": {
                    "Data": html
                }
            }
        }
    )