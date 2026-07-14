from datetime import datetime


class InputValidator:

    @staticmethod
    def validate(field, value, context):
        value = value.strip()

        # Empty input works for ALL fields
        if not value:
            return {
                "valid": False,
                "value": None,
                "message": "⚠ I didn't receive any input.\n\nPlease answer the question."
            }

        if field == "leave_type":
            return InputValidator.validate_leave_type(value)

        elif field == "reason":
            return InputValidator.validate_reason(value)

        elif field == "start_date":
            return InputValidator.validate_start_date(value)

        elif field == "end_date":
            return InputValidator.validate_end_date(value, context)

        elif field == "confirmation":
            return InputValidator.validate_confirmation(value)

        return {
            "valid": True,
            "value": value,
            "message": None
        }

    # ----------------------------------------------------
    # Leave Type
    # ----------------------------------------------------

    @staticmethod
    def validate_leave_type(value):

        valid_types = {
            "annual": "annual",
            "casual": "casual",
            "sick": "sick",
            "medical": "sick",
            "medical leave": "sick"
        }

        cleaned = value.lower()

        if cleaned in valid_types:
            return {
                "valid": True,
                "value": valid_types[cleaned],
                "message": None
            }

        return {
            "valid": False,
            "value": None,
            "message":
                "❌ Invalid leave type.\n\n"
                "Please choose one of:\n"
                "• Annual\n"
                "• Casual\n"
                "• Sick"
        }

    # ----------------------------------------------------
    # Reason
    # ----------------------------------------------------

    @staticmethod
    def validate_reason(value):

        if len(value.strip()) < 3:
            return {
                "valid": False,
                "value": None,
                "message":
                    "❌ Please provide a valid reason for your leave."
            }

        return {
            "valid": True,
            "value": value,
            "message": None
        }

    # ----------------------------------------------------
    # Start Date
    # ----------------------------------------------------

    @staticmethod
    def validate_start_date(value):

        try:
            datetime.strptime(value, "%Y-%m-%d")

            return {
                "valid": True,
                "value": value,
                "message": None
            }

        except ValueError:

            return {
                "valid": False,
                "value": None,
                "message":
                    "❌ Invalid date format.\n\n"
                    "Please enter the date in YYYY-MM-DD format.\n\n"
                    "Example:\n2026-07-15"
            }

    # ----------------------------------------------------
    # End Date
    # ----------------------------------------------------

    @staticmethod
    def validate_end_date(value, context):

        try:

            end_date = datetime.strptime(value, "%Y-%m-%d")

        except ValueError:

            return {
                "valid": False,
                "value": None,
                "message":
                    "❌ Invalid date format.\n\n"
                    "Please enter the date in YYYY-MM-DD format."
            }

        start_date = context.get("start_date")

        if start_date:

            try:

                start_date = datetime.strptime(start_date, "%Y-%m-%d")

                if end_date < start_date:

                    return {
                        "valid": False,
                        "value": None,
                        "message":
                            "❌ End date cannot be earlier than the start date."
                    }

            except Exception:
                pass

        return {
            "valid": True,
            "value": value,
            "message": None
        }

    # ----------------------------------------------------
    # Confirmation
    # ----------------------------------------------------

    @staticmethod
    def validate_confirmation(value):

        value = value.lower().strip()

        yes_words = {
            "yes",
            "y",
            "yeah",
            "yep",
            "ok",
            "okay",
            "sure",
            "submit",
            "confirm",
            "go ahead"
        }

        no_words = {
            "no",
            "n",
            "cancel",
            "stop",
            "never mind"
        }

        if value in yes_words:

            return {
                "valid": True,
                "value": "yes",
                "message": None
            }

        if value in no_words:

            return {
                "valid": True,
                "value": "no",
                "message": None
            }

        return {
            "valid": False,
            "value": None,
            "message":
                "❌ Please reply with:\n\n"
                "YES - to submit the leave request\n"
                "NO - to cancel the leave request"
        }