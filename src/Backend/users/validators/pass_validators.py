import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class UppercaseValidator(object):

    def __init__(self, min_upper=1):
            self.min_upper = min_upper

    def validate(self, password, user=None):
        all_upper = re.findall('[A-Z]', password)
        if not all_upper or len(all_upper) < self.min_upper:
            raise ValidationError(
                _("The password must contain at least {min_upper} uppercase letter, A-Z.").format(min_upper=self.min_upper),
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_upper)d uppercase letter, A-Z."
            % {'min_upper': self.min_upper}
        )

class LowercaseValidator(object):

    def __init__(self, min_lower=3):
            self.min_lower = min_lower

    def validate(self, password, user=None):
        min_lower = re.findall('[a-z]', password)
        if not min_lower or len(min_lower) < self.min_lower:
            raise ValidationError(
                _("The password must contain at least {min_lower} lowercase letter, a-z.").format(min_lower=self.min_lower)
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_lower)d lowercase letter, a-z."
            % {'min_lower': self.min_lower}
        )

class NumericValidator(object):

    def __init__(self, min_numeric=3):
            self.min_numeric = min_numeric

    def validate(self, password, user=None):
        all_numeric = re.findall('[0-9]', password)
        if not all_numeric or len(all_numeric) < self.min_numeric:
            raise ValidationError(
                _("The password must contain at least {min_numeric} numeric character, 0-9.").format(min_numeric=self.min_numeric),
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_numeric)d numeric character, 0-9."
            % {'min_numeric': self.min_numeric}
        )
    
class SpecialCharValidator(object):

    def __init__(self, min_special=1):
            self.min_special = min_special

    def validate(self, password, user=None):
        all_special = re.findall('[@#$%!^&*]', password)
        if not all_special or len(all_special) < self.min_special:
            raise ValidationError(
                _(("The password must contain at least {min_special} special character: " +
                  "@#$%!^&*").format(min_special=self.min_special)),
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_special)d special character: " +
            "@#$%!^&*"
            % {'min_special': self.min_special}
        )